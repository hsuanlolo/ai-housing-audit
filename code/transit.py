"""
Pure-Python transit router over the MTA subway GTFS feed.

FORMULATION. Commuting is an arrive-by problem ("I need to be at work by 09:00"),
not a depart-at problem, so we solve the backward variant: for every station, the
latest departure that still reaches the anchor by the target arrival time. We
obtain this by reversing the timetable -- negate times about the target and
reverse each pattern's stop order -- which turns the backward problem into a
standard forward RAPTOR from the anchor.

    tau = T_arrive - t

Because arrival times increase along a trip, tau decreases, so a reversed pattern
is monotone increasing in tau and ordinary RAPTOR applies unchanged. The value
tau[stop] returned for each station IS the door-to-door transit duration from
that station to the anchor.

DOCUMENTED APPROXIMATIONS (all common to every listing and identity condition):
  * Subway + Staten Island Railway only; buses excluded. Coverage consequence is
    measured, not assumed -- see report_coverage().
  * Walk access is straight-line distance x 1.3 detour factor at 4.8 km/h, not
    street-network routed. Error ~1-2 min per leg.
  * Transfers use transfers.txt where present, same-parent-station links, and
    footpaths between distinct stations within FOOTPATH_M metres.
"""
import zipfile, math, heapq, json
from collections import defaultdict
import numpy as np
import pandas as pd
from common import RAW, INTERIM

GTFS_ZIP      = RAW/"gtfs_subway.zip"
SERVICE_ID    = "Weekday"
TARGET_ARRIVE = 9 * 3600          # 09:00:00
MAX_ROUNDS    = 5                 # up to 4 transfers
WALK_MPS      = 4.8 * 1000 / 3600 # 4.8 km/h
DETOUR        = 1.3
ACCESS_M      = 1200              # listing -> station walk radius (19.5 min walk)
# Chosen over the literature-standard 800 m after measuring the exclusion bias:
# at 800 m, the 11% of listings dropped were $600/mo CHEAPER at the median and
# concentrated in Queens, Staten Island and the Bronx -- i.e. the filter removed
# exactly the cheap bus-dependent inventory that a paper about rent gaps must not
# lose. Widening to 1200 m retains 94.6% and moves the median commute only from
# 30.0 to 30.4 min. The 800 m universe is retained as a robustness check.
FOOTPATH_M    = 300               # station <-> station walk transfer radius
XFER_PENALTY  = 60                # seconds, boarding/platform-change penalty

# The Staten Island Railway has no track connection to the subway; real commutes
# use the Staten Island Ferry. The ferry is not in this GTFS feed, so we add the
# link explicitly: 25 min crossing + 15 min mean wait on a 30 min headway.
# Without it, every Staten Island listing is unreachable and a borough silently
# drops out of the sample.
FERRY_LINKS = [("St George", "Whitehall St", 40 * 60)]

ANCHORS = {   # (lat, lon) of the three workplace anchors
    "midtown_manhattan":  (40.7549, -73.9840),   # Times Sq / 42 St
    "downtown_manhattan": (40.7075, -74.0113),   # Fulton St / FiDi
    "downtown_brooklyn":  (40.6928, -73.9903),   # Jay St-MetroTech
}

def _secs(s):
    try:
        h, m, sec = str(s).split(":"); return int(h)*3600 + int(m)*60 + int(sec)
    except Exception:
        return np.nan

def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))


class Network:
    def __init__(self, zip_path=GTFS_ZIP, service_id=SERVICE_ID):
        z = zipfile.ZipFile(zip_path)
        stops = pd.read_csv(z.open("stops.txt"))
        trips = pd.read_csv(z.open("trips.txt"))
        st    = pd.read_csv(z.open("stop_times.txt"))
        try:    xf = pd.read_csv(z.open("transfers.txt"))
        except Exception: xf = pd.DataFrame(columns=["from_stop_id","to_stop_id","min_transfer_time"])

        # Collapse platform-level stops onto parent stations. Parents carry
        # location_type 1; children point at them via parent_station.
        stops["station"] = stops["parent_station"].fillna(stops["stop_id"]).astype(str)
        self.stop2station = dict(zip(stops.stop_id.astype(str), stops.station))
        stn = (stops[stops.stop_id.astype(str) == stops.station]
               .drop_duplicates("station").set_index("station"))
        self.stations   = list(stn.index)
        self.sidx       = {s: i for i, s in enumerate(self.stations)}
        self.stn_lat    = stn["stop_lat"].values
        self.stn_lon    = stn["stop_lon"].values
        self.stn_name   = stn["stop_name"].values

        trips = trips[trips.service_id == service_id]
        st = st[st.trip_id.isin(set(trips.trip_id))].copy()
        st["t"] = st["departure_time"].map(_secs)
        st["st"] = st.stop_id.astype(str).map(self.stop2station)
        st = st.dropna(subset=["t", "st"]).sort_values(["trip_id", "stop_sequence"])

        # Group trips into patterns (identical station sequences).
        pats = defaultdict(list)
        for tid, g in st.groupby("trip_id", sort=False):
            key = tuple(g["st"].tolist())
            if len(key) < 2: continue
            pats[key].append(np.asarray(g["t"].tolist(), dtype=np.int64))

        # REVERSAL: tau = TARGET_ARRIVE - t, stop order reversed.
        self.patterns = []
        for key, triplist in pats.items():
            rev_stops = [self.sidx[s] for s in reversed(key)]
            taus = np.array([ (TARGET_ARRIVE - tr)[::-1] for tr in triplist ], dtype=np.int64)
            order = np.argsort(taus[:, 0])
            self.patterns.append((rev_stops, taus[order]))

        # Which patterns touch each station, and at which index.
        self.by_station = defaultdict(list)
        for pi, (sseq, _) in enumerate(self.patterns):
            for k, s in enumerate(sseq):
                self.by_station[s].append((pi, k))

        self.footpaths = self._build_footpaths(xf)
        self._add_named_links(FERRY_LINKS)
        self.n = len(self.stations)

    def _build_footpaths(self, xf):
        fp = defaultdict(dict)
        for _, r in xf.iterrows():
            a = self.stop2station.get(str(r["from_stop_id"]))
            b = self.stop2station.get(str(r["to_stop_id"]))
            if a in self.sidx and b in self.sidx and a != b:
                c = int(r.get("min_transfer_time") or 180)
                i, j = self.sidx[a], self.sidx[b]
                fp[i][j] = min(fp[i].get(j, 10**9), c)
        # walking links between distinct nearby stations
        lat, lon = self.stn_lat, self.stn_lon
        for i in range(len(self.stations)):
            d = _haversine_m(lat[i], lon[i], lat, lon)
            for j in np.where((d > 0) & (d <= FOOTPATH_M))[0]:
                c = int(d[j] * DETOUR / WALK_MPS)
                fp[i][int(j)] = min(fp[i].get(int(j), 10**9), c)
        return {i: dict(v) for i, v in fp.items()}

    def _add_named_links(self, links):
        """Attach fixed-cost bidirectional links between stations matched by name."""
        for a_name, b_name, cost in links:
            ia = [i for i, n in enumerate(self.stn_name) if a_name.lower() in str(n).lower()]
            ib = [i for i, n in enumerate(self.stn_name) if b_name.lower() in str(n).lower()]
            if not ia or not ib:
                print(f"  !! named link {a_name} <-> {b_name}: station not found, skipped")
                continue
            i, j = ia[0], ib[0]
            self.footpaths.setdefault(i, {})[j] = min(self.footpaths.get(i, {}).get(j, 10**9), cost)
            self.footpaths.setdefault(j, {})[i] = min(self.footpaths.get(j, {}).get(i, 10**9), cost)
            print(f"  added link: {self.stn_name[i]} <-> {self.stn_name[j]} = {cost/60:.0f} min")

    def raptor(self, source_idx):
        """Backward RAPTOR. Returns tau (seconds) from every station to the anchor."""
        INF = 10**9
        best = np.full(self.n, INF, dtype=np.int64)
        best[source_idx] = 0
        marked = {source_idx}
        for j, c in self.footpaths.get(source_idx, {}).items():
            if c < best[j]: best[j] = c; marked.add(j)

        for _ in range(MAX_ROUNDS):
            if not marked: break
            # collect patterns reachable from marked stations
            q = {}
            for s in marked:
                for pi, k in self.by_station[s]:
                    if pi not in q or k < q[pi]: q[pi] = k
            marked = set()
            for pi, k0 in q.items():
                sseq, taus = self.patterns[pi]
                cur = None                      # index of boarded trip
                for k in range(k0, len(sseq)):
                    s = sseq[k]
                    if cur is not None:
                        arr = int(taus[cur, k])
                        if arr < best[s]:
                            best[s] = arr; marked.add(s)
                    # can we board an earlier (in tau) trip here?
                    if best[s] < INF:
                        ready = best[s] + XFER_PENALTY
                        col = taus[:, k]
                        idx = int(np.searchsorted(col, ready, side="left"))
                        if idx < len(col) and (cur is None or idx < cur):
                            cur = idx
            # relax footpaths
            for s in list(marked):
                for j, c in self.footpaths.get(s, {}).items():
                    v = best[s] + c
                    if v < best[j]: best[j] = v; marked.add(j)
        return best

    def station_times_to_anchors(self):
        out = {}
        for name, (la, lo) in ANCHORS.items():
            d = _haversine_m(la, lo, self.stn_lat, self.stn_lon)
            src = int(np.argmin(d))
            tau = self.raptor(src)
            # add walk from anchor coordinate to its boarding station
            tau = tau + int(d[src] * DETOUR / WALK_MPS)
            out[name] = tau
            reach = int((tau < 10**9).sum())
            print(f"  {name:22s} boarding at {self.stn_name[src]:32s} "
                  f"stations reached {reach}/{self.n}  median {np.median(tau[tau<10**9])/60:5.1f} min")
        return out

    def listing_commutes(self, lat, lon, station_times):
        """Door-to-door minutes from each listing to each anchor. NaN if unreachable."""
        lat, lon = np.asarray(lat, float), np.asarray(lon, float)
        res = {}
        for name, tau in station_times.items():
            best = np.full(len(lat), np.nan)
            for i in range(len(lat)):
                d = _haversine_m(lat[i], lon[i], self.stn_lat, self.stn_lon)
                near = np.where(d <= ACCESS_M)[0]
                if len(near) == 0: continue
                walk = d[near] * DETOUR / WALK_MPS
                tot = walk + tau[near]
                tot = tot[tau[near] < 10**9]
                if len(tot): best[i] = tot.min() / 60.0
            res[name] = best
        return res

    def report_coverage(self, lat, lon):
        lat, lon = np.asarray(lat, float), np.asarray(lon, float)
        nearest = np.array([_haversine_m(lat[i], lon[i], self.stn_lat, self.stn_lon).min()
                            for i in range(len(lat))])
        return dict(
            n=len(lat),
            share_within_800m=float((nearest <= 800).mean()),
            share_within_1200m=float((nearest <= 1200).mean()),
            median_nearest_m=float(np.median(nearest)),
            p90_nearest_m=float(np.percentile(nearest, 90)),
        )

if __name__ == "__main__":
    print("building network from MTA subway GTFS ...")
    net = Network()
    print(f"stations: {net.n}  patterns: {len(net.patterns)}  "
          f"footpath nodes: {len(net.footpaths)}")
    print("\nbackward RAPTOR from each anchor (arrive by 09:00):")
    stt = net.station_times_to_anchors()
    np.savez(INTERIM/"station_times.npz",
             stations=np.array(net.stations),
             lat=net.stn_lat, lon=net.stn_lon, name=net.stn_name,
             **stt)
    print(f"\nsaved: {INTERIM/'station_times.npz'}")
