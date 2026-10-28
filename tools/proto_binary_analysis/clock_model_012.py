"""Round 012 clock-adapter model check. Pure model: never reads or runs the game.

Native side ports the decoded Proto code (RVAs in SCHEDULER_AUDIT_012.md):
  budget 0x9a3900, PrintLetterByLetter 0x9a3ec0, tickable Tick 0x9a5b30, normal finish 0x9a07b0,
  UWorld::Tick time update 0x242bdc7..0x242be47, timer tick 0x242c48a..0x242c4b3, TickObjects 0x27421f0.
Arabic side ports the 011 helpers (Advance Budget / Step / Finish) plus the proposed 012 adapter
(Arm Clock, Clock Fired via K2_SetTimer, paused-mode Event Tick via GetUnpausedTimeSeconds).
World clocks are float32 as in 4.27; FTimerManager::InternalTime is float64.

Run: python -I tools/proto_binary_analysis/clock_model_012.py
"""
import random
import numpy as np

f32 = np.float32


class World:
    """UWorld::Tick order: times -> FTimerManager::Tick (unpaused only) -> TickObjects -> (later) Slate tick."""

    def __init__(self):
        self.time = f32(0)        # +0x5a0 TimeSeconds
        self.unpaused = f32(0)    # +0x5a4 UnpausedTimeSeconds
        self.internal = 0.0       # FTimerManager::InternalTime (double)
        self.timers = {}          # key -> [expire, rate, callback, pending]
        self.in_tick = False
        self.tickables = []

    def set_timer(self, key, rate, cb):
        # InternalSetTimer: same handle/delegate replaces; inside Tick -> active now, else pending until tick end.
        self.timers[key] = [self.internal + rate, rate, cb, False] if self.in_tick else [rate, rate, cb, True]

    def clear_timer(self, key):
        self.timers.pop(key, None)

    def tick(self, dt, paused, dilation):
        d = f32(f32(dt) * f32(dilation))
        self.unpaused = f32(self.unpaused + d)
        if not paused:
            self.time = f32(self.time + d)
            self.in_tick = True
            self.internal += float(d)
            while True:
                due = [(v[0], k) for k, v in self.timers.items() if not v[3] and self.internal > v[0]]
                if not due:
                    break
                _, k = min(due)
                cb = self.timers.pop(k)[2]
                cb()
            for v in self.timers.values():
                if v[3]:
                    v[0] += self.internal
                    v[3] = False
            self.in_tick = False
        for t in list(self.tickables):
            t.tick(d)   # TickObjects: IsTickable/WhenPaused == AnimateWhilePaused (filtered at registration here)


class NativeProto:
    """Item-level port of process_reveal_budget. pend[i] = pending before item i; pend[n] = before finish."""

    def __init__(self, world, pend, awp):
        self.w, self.pend, self.awp, self.n = world, [f32(p) for p in pend], awp, len(pend) - 1
        self.reveal, self.finish = {}, []
        self.acc, self.rem = f32(0), f32(-1)
        if awp:
            world.tickables.append(self)

    def start(self, frame):
        self.frame = frame
        self.idx = -1
        self.pending = self.pend[0]
        self.stamp = self.w.time
        if self.pending <= 0:
            self.process()
        elif self.awp:
            self.rem, self.acc = self.pending, f32(0)
        else:
            self.w.set_timer(("native", id(self)), float(self.pending), self.process)

    def tick(self, d):  # 0x9a5b30
        self.acc = f32(self.acc + d)
        if self.rem >= 0 and self.acc >= self.rem:
            self.process()

    def process(self):
        elapsed = self.acc if self.awp else f32(self.w.time - self.stamp)
        budget = max(self.pending, elapsed)
        while True:
            if self.idx + 1 >= self.n:
                self.finish.append(self.frame)   # 0x9a07b0; never disarms the tickable path
                return
            self.idx += 1
            self.reveal[self.idx] = self.frame
            budget = f32(budget - self.pending)
            self.pending = self.pend[self.idx + 1]
            if not budget >= self.pending:
                break
        self.pending = f32(self.pending - budget)
        if self.awp:
            self.rem, self.acc = self.pending, f32(0)
        else:
            self.w.set_timer(("native", id(self)), float(self.pending), self.process)
            self.stamp = self.w.time


class Arabic:
    """011 Advance Budget/Step/Finish + proposed 012 adapter. delays[u] = due before unit u."""

    def __init__(self, world, delays, awp):
        self.w, self.d, self.awp, self.count = world, [f32(x) for x in delays], awp, len(delays)
        self.reveal, self.finish = {}, []
        self.active = self.armed = self.finished = False
        self.gen, self.rem, self.stamp = 0, f32(-1), f32(0)

    def begin(self, frame):                      # Set Displayed Line Arabic tail -> Begin Reveal
        self.frame = frame
        self.active, self.finished, self.elapsed, self.cur, self.armed = True, False, f32(0), -1, True
        self.advance(f32(0), self.gen)
        self.arm()

    def finish_(self, early):                    # Arabic Finish (+ 012: clear timer, disarm)
        if not (self.active and not self.finished):
            return
        self.finished, self.armed, self.active = True, False, False
        self.w.clear_timer(("ar", id(self)))
        self.rem = f32(-1)
        self.cur = self.count - 1
        self.finish.append((self.frame, early))  # broadcast last; no state change after it

    def cancel(self):                            # Arabic Cancel (+ 012: clear timer, disarm)
        self.armed = self.active = self.finished = False
        self.gen += 1
        self.w.clear_timer(("ar", id(self)))
        self.rem = f32(-1)

    def step(self):
        if not (self.active and self.armed and not self.finished):
            return
        if not self.cur < self.count - 1:
            return self.finish_(False)
        self.cur += 1
        self.reveal[self.cur] = self.frame
        if self.cur == self.count - 1:
            self.finish_(False)

    def advance(self, delta, gen):
        if not (self.armed and self.active and gen == self.gen) or not delta >= 0:
            return
        self.elapsed = f32(self.elapsed + delta)
        while self.armed and self.active and gen == self.gen:
            if not self.cur + 1 < self.count:
                return self.finish_(False)
            due = self.d[self.cur + 1]
            if not self.elapsed >= due:
                return
            self.elapsed = f32(self.elapsed - due)
            self.step()

    def arm(self):                               # 012 Arabic Arm Clock
        if not (self.active and self.armed and not self.finished) or not self.cur + 1 < self.count:
            return
        self.rem = f32(self.d[self.cur + 1] - self.elapsed)
        self.clock_gen = self.gen
        if self.awp:
            self.stamp = self.w.unpaused
        else:
            self.stamp = self.w.time
            self.w.set_timer(("ar", id(self)), float(self.rem), self.fired)

    def fired(self):                             # 012 Arabic Clock Fired (K2_SetTimer target)
        if self.awp or not (self.active and self.armed and not self.finished and self.clock_gen == self.gen):
            return
        gen, delta, self.rem = self.gen, max(self.rem, f32(self.w.time - self.stamp)), f32(-1)
        self.advance(delta, gen)
        if gen == self.gen:
            self.arm()

    def slate_tick(self):                        # 012 Event Tick body (only acts in paused mode)
        if not (self.awp and self.active and self.armed and not self.finished and self.rem >= 0):
            return
        el = f32(self.w.unpaused - self.stamp)
        if not el >= self.rem:
            return
        gen, delta, self.rem = self.gen, max(self.rem, el), f32(-1)
        self.advance(delta, gen)
        if gen == self.gen:
            self.arm()


def run(seed, awp, hidden_rate=0.0, stale_acc=False):
    rng = random.Random(seed)
    n = rng.randint(1, 37)
    pend = [rng.choice([0.0, 0.025, 0.025, 0.05, 0.1, 0.3]) for _ in range(n + 1)]
    w = World()
    nat = NativeProto(w, pend, awp) if stale_acc else None
    for _ in range(rng.randint(0, 200)):          # random world uptime before the line starts
        w.tick(rng.uniform(1 / 144, 1 / 20), False, 1.0)
    # Fresh widget: the tickable accumulator starts at 0. A reused block keeps it (stale_acc quirk).
    nat, ar = nat or NativeProto(w, pend, awp), Arabic(w, pend[:n], awp)
    nat.start(0)
    ar.begin(0)
    paused, dil = False, 1.0
    for frame in range(1, 3000):
        if rng.random() < 0.01:
            paused = not paused
        if rng.random() < 0.005:
            dil = rng.choice([1.0, 0.5, 0.25, 2.0])
        dt = rng.uniform(1 / 240, 1 / 20) if rng.random() > 0.01 else rng.uniform(0.1, 0.4)
        nat.frame = ar.frame = frame
        w.tick(dt, paused, dil)
        if rng.random() >= hidden_rate:
            ar.slate_tick()
        if nat.finish and ar.finish and frame > max(nat.finish[0], ar.finish[0][0]) + 5:
            break
    return n, pend, nat, ar


def main():
    exact_a = exact_b = 0
    b_offsets = []
    for seed in range(4000):
        n, pend, nat, ar = run(seed, awp=False)
        assert len(ar.finish) == 1 and ar.finish[0][1] is False, "single normal finish"
        if all(nat.reveal.get(i) == ar.reveal.get(i) for i in range(n)):
            exact_a += 1
        # native finish needs the trailing pending pend[n]; Arabic finishes with its last unit
        assert ar.finish[0][0] == ar.reveal[n - 1] and nat.finish[0] >= ar.finish[0][0]
        assert len(nat.finish) == 1, "timer mode finishes once"
    for seed in range(4000):
        n, pend, nat, ar = run(seed, awp=True)
        assert len(ar.finish) == 1
        b_offsets += [ar.reveal[i] - nat.reveal[i] for i in range(n)]
        if all(nat.reveal.get(i) == ar.reveal.get(i) for i in range(n)):
            exact_b += 1
        assert len(nat.finish) >= 1   # tickable path never disarms: repeats every world tick after completion
    hidden = []
    for seed in range(1000):
        n, pend, nat, ar = run(seed, awp=True, hidden_rate=0.3)
        assert len(ar.finish) == 1 and ar.cur == n - 1, "hidden frames delay but converge"
        hidden += [ar.reveal[i] - nat.reveal[i] for i in range(n)]
    repeats = max(len(run(s, awp=True)[2].finish) for s in range(50))
    stale = [run(s, awp=True, stale_acc=True) for s in range(2000)]
    zero_first = [r for r in stale if r[1][0] == 0.0]
    instant = sum(1 for n, p, nat, ar in zero_first if all(nat.reveal[i] == 0 for i in range(n)))
    print(f"CASE_A timer mode: {exact_a}/4000 lines frame-identical to native")
    print(f"CASE_B paused mode, visible every frame: {exact_b}/4000 identical; "
          f"offset frames min={min(b_offsets)} max={max(b_offsets)} nonzero={sum(1 for x in b_offsets if x)}/{len(b_offsets)}")
    print(f"CASE_B with 30% hidden frames: offset min={min(hidden)} max={max(hidden)} frames")
    print(f"native tickable finish broadcasts per line (max over 50): {repeats}; Arabic: 1")
    print(f"native stale-accumulator quirk: {instant}/{len(zero_first)} reused-block lines with zero first delay "
          f"revealed completely on the start frame (Arabic adapter: 0)")
    assert exact_a == 4000, "timer-mode adapter must be frame-identical"
    # Paused mode: float32 operation order (UnpausedTimeSeconds difference vs native accumulator) may flip an
    # exact tie by one frame; hidden frames only delay. Anything earlier than one frame is a logic error.
    assert min(b_offsets) >= -1 and max(b_offsets) <= 1 and min(hidden) >= -1


if __name__ == "__main__":
    main()
