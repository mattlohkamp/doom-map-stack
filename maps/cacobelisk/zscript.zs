version "4.10"

// Cacobelisk's own script (dms packs it into this map's WAD; it runs on this map only).
// In-game note #1 and the follow-up in chat (2026-11-22): the start is a broken elevator. The switch ahead of the platform lowers it
// (Floor_LowerByValue on CAR_TAG, set in map.py) down the shaft; when it lands, its light starts
// to flicker and the platform throws sparks (with their sound) off the shaft walls, for good.

class CacobeliskElevator : EventHandler
{
	const CAR_TAG = 1;          // the car's sector tag (map.py CAR_TAG)
	const LANDED_Z = -256;      // its floor once down (map.py -DROP)

	const CLOSET_TAG = 2;       // the start closet (map.py CLOSET_TAG)

	// The closet breathes: its light fades between dim and dimmer, 3 s each way (Light_Glow: tag,
	// upper, lower, tics), from the moment the level loads (again after H).
	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame) return;   // a saved game has it running already
		Level.ExecuteSpecial(Light_Glow, null, null, false, CLOSET_TAG, 92, 60, 105);
	}

	bool riding;
	bool broken;
	int landedAt;       // Level.maptime of the landing (CacobeliskObelisks starts its sequence from it)
	int nextSpark;

	const SECRET_TAG = 3;       // the entry secret's panel (map.py SECRET_TAG)
	const TARGET_TID = 301;     // the target's red pulse (map.py TARGET_TID)
	const SLOT_TAG = 5;         // the target's slot (map.py TARGET_SLOT_TAG)
	const SLOT_DROP = 16;       // how far its ceiling comes down to shut it
	const DUST_PUFFS = 10;      // note #39

	// The entry secret's target (the valve wheel over the start door, map.py) glows until it's shot:
	// then its wall goes back to the closet's own light and its pulse goes out.
	void DimTarget(Line ln)
	{
		Side sd = ln.sidedef[0];
		if (sd != null)
		{
			sd.Light = 0;
			sd.Flags &= ~Side.WALLF_ABSLIGHTING;
		}
		let it = Level.CreateActorIterator(TARGET_TID);
		Actor l;
		while ((l = it.Next()) != null)
			l.Deactivate(null);
		// Note #39: a little cloud of dust puffs out of the secret panel as it starts to open, drifts
		// into the closet and fades.
		let panels = Level.CreateSectorTagIterator(SECRET_TAG);
		int pi;
		while ((pi = panels.Next()) >= 0)
		{
			Sector door = Level.sectors[pi];
			Vector2 c = door.centerspot;
			double z0 = door.floorplane.ZAtPoint(c);
			double into = (c.x > 32) ? -1 : 1;      // towards the closet's middle (x 32)
			for (int n = 0; n < DUST_PUFFS; n++)
			{
				Actor puff = Actor.Spawn("CacobeliskDust", (c.x + into * 6, c.y + FRandom(-16, 16), z0 + FRandom(4, 52)), NO_REPLACE);
				if (puff != null)
					puff.vel = (into * FRandom(0.3, 1.1), FRandom(-0.25, 0.25), FRandom(0.02, 0.25));
			}
		}
		// Note #35: a block drops over the target: the slot's ceiling (72) comes down to the beam's (56).
		Level.ExecuteSpecial(Ceiling_LowerByValue, null, null, false, SLOT_TAG, 16, SLOT_DROP);
		Console.Printf("[DMS] CacobeliskElevator: the target was shot; the secret panel opens");
	}

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		if (ln != null && ln.special == Door_Open && ln.args[0] == SECRET_TAG)
			DimTarget(ln);
		// The top switch (Floor_LowerByValue) or the bottom call switch (Floor_MoveToValue, note #10).
		if (ln != null && (ln.special == Floor_LowerByValue || ln.special == Floor_MoveToValue)
			&& ln.args[0] == CAR_TAG && !riding)
		{
			riding = true;
			Console.Printf("[DMS] CacobeliskElevator: the platform is going down");
			LockSwitches(ln);
			// Note #114 (2026-11-24): the ride made no sound. The script plays it now (and the map silences
			// the engine's own floor sound for these sectors, so it can't double): a clunk as it starts, a
			// low grinding loop that rides down with the car, a clunk when it lands.
			Sector car = FindCar();
			if (car != null)
			{
				rideSound = Actor.Spawn("MapSpot", (car.centerspot.x, car.centerspot.y, car.floorplane.ZAtPoint(car.centerspot)));
				if (rideSound != null)
				{
					rideSound.A_StartSound("plats/pt1_strt", CHAN_5, 0, 1.0, ATTN_NORM, 0.8);
					rideSound.A_StartSound("plats/pt1_mid", CHAN_BODY, CHANF_LOOPING, 0.9, ATTN_NORM, 0.75);
				}
			}
		}
	}

	// Note #12: once either switch is used, both are done for good: the other one loses its special
	// (from the bottom of the shaft the top switch could still be reached, and lowered the platform
	// another 256) and shows its "on" texture, like the one that was pressed.
	// Note #34: once either switch has been used, both are shut away behind metal, so it's plain they
	// are a one-time thing: a second after, the bottom niche's sill rises to its top (the sill's face is
	// the metal panel: map.py), and the top switch, whose niche is the way down and can't shut, has its
	// plate replaced by the niche's own metal.
	const NICHE_SHUT_TAG = 4;    // the bottom niche (map.py CALL_NICHE_TAG)
	const NICHE_SHUT_RISE = 32;  // its height
	const SHUT_DELAY = 0;        // note #40: at once (was a second later)
	const SHUT_SPEED = 64;       // and fast: the panel snaps shut (8 units a tic)
	const SHUTTER_TAG = 6;       // the top switch's shutter (map.py SHUTTER_TAG)
	const PULSE_TID = 302;       // the top switch's pulsing light (map.py SWITCH_PULSE_TID)
	Line upperSwitch;
	int shutAt;
	Actor rideSound;             // note #114: the spot the ride's sound plays from; it goes down with the car

	void ShutSwitches()
	{
		// Note #37: the bottom niche too (its sill rose at first, and its face ran down the whole wall).
		Level.ExecuteSpecial(Ceiling_LowerByValue, null, null, false, NICHE_SHUT_TAG, SHUT_SPEED, NICHE_SHUT_RISE);
		// Note #36: the top switch isn't swapped for plain metal any more: a panel comes down in front of
		// it (the shutter's ceiling, from the niche's top to its sill), and its pulsing light goes out.
		Level.ExecuteSpecial(Ceiling_LowerByValue, null, null, false, SHUTTER_TAG, SHUT_SPEED, NICHE_SHUT_RISE);
		let it = Level.CreateActorIterator(PULSE_TID);
		Actor glow;
		while ((glow = it.Next()) != null)
			glow.Deactivate(null);
		trackAt = Level.maptime + 8;
		Console.Printf("[DMS] CacobeliskElevator: the switches are shut behind metal");
	}

	// Note #49: the top switch's wall is one texture (the switch, cement round its plate) all the way
	// down the shaft below it, so riding down the player saw cement where the elevator's track should
	// be. Once the panel has covered the plate (trackAt), the wall behind it becomes the track's metal.
	int trackAt;

	void WallToTrack()
	{
		if (upperSwitch == null)
			return;
		TextureID track = TexMan.CheckForTexture("SUPPORT3", TexMan.Type_Wall);
		TextureID plateOff = TexMan.CheckForTexture("SW1GRAY", TexMan.Type_Wall);
		TextureID plateOn = TexMan.CheckForTexture("SW2GRAY", TexMan.Type_Wall);
		for (int s = 0; s < 2; s++)
		{
			Side sd = upperSwitch.sidedef[s];
			if (sd == null)
				continue;
			for (int part = Side.top; part <= Side.bottom; part++)
			{
				if (sd.GetTexture(part) == plateOff || sd.GetTexture(part) == plateOn)
					sd.SetTexture(part, track);
			}
		}
	}

	bool IsShutter(Sector s)
	{
		if (s == null)
			return false;
		let it = Level.CreateSectorTagIterator(SHUTTER_TAG);
		int i;
		while ((i = it.Next()) >= 0)
		{
			if (Level.sectors[i] == s)
				return true;
		}
		return false;
	}

	void LockSwitches(Line used)
	{
		TextureID off = TexMan.CheckForTexture("SW1GRAY", TexMan.Type_Wall);
		TextureID on = TexMan.CheckForTexture("SW2GRAY", TexMan.Type_Wall);
		shutAt = Level.maptime + SHUT_DELAY;
		for (int i = 0; i < Level.Lines.Size(); i++)
		{
			Line l = Level.Lines[i];
			// Note #120: both switches are Floor_MoveToValue now: the top one is the line in front of the shutter.
			if (l.args[0] == CAR_TAG && (l.special == Floor_LowerByValue || l.special == Floor_MoveToValue)
				&& IsShutter(l.frontsector))
				upperSwitch = l;
			if (l == used || l.args[0] != CAR_TAG
				|| (l.special != Floor_LowerByValue && l.special != Floor_MoveToValue))
				continue;
			l.special = 0;
			for (int s = 0; s < 2; s++)
			{
				Side sd = l.sidedef[s];
				if (sd == null)
					continue;
				for (int part = Side.top; part <= Side.bottom; part++)
				{
					if (sd.GetTexture(part) == off)
						sd.SetTexture(part, on);
				}
			}
		}
	}

	override void WorldTick()
	{
		if (!riding)
			return;
		if (trackAt > 0 && Level.maptime >= trackAt)
		{
			trackAt = 0;
			WallToTrack();
		}
		if (shutAt > 0 && Level.maptime >= shutAt)
		{
			shutAt = 0;
			ShutSwitches();
		}
		Sector car = FindCar();
		if (car == null)
			return;
		if (rideSound != null)
			rideSound.SetOrigin((car.centerspot.x, car.centerspot.y, car.floorplane.ZAtPoint(car.centerspot)), true);
		if (!broken)
		{
			if (car.floorplane.ZAtPoint(car.centerspot) > LANDED_Z + 0.5)
				return;
			broken = true;
			if (rideSound != null)
			{
				rideSound.A_StopSound(CHAN_BODY);
				rideSound.A_StartSound("plats/pt1_stop", CHAN_6, 0, 1.0, ATTN_NORM, 0.7);
				rideSound = null;
			}
			landedAt = Level.maptime;
			// Light_Flicker (tag, upper, lower): the car's light jumps between bright and dim.
			Level.ExecuteSpecial(Light_Flicker, null, null, false, CAR_TAG, 144, 40);
			for (int i = 0; i < 3; i++)   // the bang on landing
				Spark(car);
			nextSpark = Level.maptime + Random(20, 60);
			Console.Printf("[DMS] CacobeliskElevator: landed; the car is broken (flicker, sparks)");
			return;
		}
		if (Level.maptime >= nextSpark)
		{
			Spark(car);
			if (Random(0, 3) == 0)
				Spark(car);     // now and then two at once
			nextSpark = Level.maptime + Random(25, 140);
		}
	}

	// The platform: of the sectors tagged CAR_TAG (the platform and the switch niche's floor, which
	// go down together), the one with the lowest floor (the niche's sill is 16 higher).
	Sector FindCar()
	{
		let it = Level.CreateSectorTagIterator(CAR_TAG);
		Sector best = null;
		int i;
		while ((i = it.Next()) >= 0)
		{
			Sector s = Level.Sectors[i];
			if (best == null || s.floorplane.ZAtPoint(s.centerspot) < best.floorplane.ZAtPoint(best.centerspot))
				best = s;
		}
		return best;
	}

	// A spark (UZDoom's Spark: a burst of particles and the "world/spark" sound) off a random spot on
	// one of the shaft walls, just above the landed platform, spraying across it.
	void Spark(Sector car)
	{
		Array<Line> walls;
		for (int i = 0; i < car.lines.Size(); i++)
		{
			// The shaft's walls: blocking lines onto the solid blocks around it (map.py shaft_side).
			if (car.lines[i].sidedef[1] == null || (car.lines[i].flags & Line.ML_BLOCKING))
				walls.Push(car.lines[i]);
		}
		if (walls.Size() == 0)
			return;
		Line w = walls[Random(0, walls.Size() - 1)];
		Vector2 d = w.delta;
		Vector2 inward = (d.y, -d.x).Unit();   // the front (car) side is on the line's right
		Vector2 at = w.v1.p + d * FRandom(0.1, 0.9) + inward * 4;
		double z = car.floorplane.ZAtPoint(at) + FRandom(12, 56);
		// A few spark actors, reused in turn (destroying one could cut its sound short).
		Actor s;
		if (sparks.Size() < 4)
		{
			s = Actor.Spawn("Spark", (at.x, at.y, z));
			if (s == null)
				return;
			sparks.Push(s);
		}
		else
		{
			s = sparks[sparkTurn++ % sparks.Size()];
			s.SetOrigin((at.x, at.y, z), false);
		}
		s.angle = atan2(inward.y, inward.x);
		s.args[0] = Random(16, 40);
		s.Activate(null);
	}

	Array<Actor> sparks;
	int sparkTurn;
}

// The mapper, 2026-11-22: the reveal is a show watched from the elevator. A few beats after it lands
// and breaks (CacobeliskElevator), the obelisks are revealed one at a time, nearest pair first, west then
// east, a pause between each: all but the switch obelisk, which is revealed only when the player takes
// the shotgun from its altar (thing id SHOTGUN_TID). (Until then, from note #8, each pair was revealed
// as the player walked past it.)
// Note #8: the obelisks' reveal. Each starts as a plain pillar up to the ceiling (its sleeve, map.py
// monolith). Its sleeve sinks slowly into its base (Floor_LowerToLowest: down to the base, the
// lowest floor beside them), down out of their slots in the ceiling, uncovering the carved slabs, a
// cacodemon on the one that has one (note #11: only the switch obelisk; spawned now, still hidden inside
// the sleeve),
// and their glow lights come on. Pairs go one at a time as they're passed. Everything is found from
// the map: pair i's sleeves are tagged SLEEVE_TAG + i, the slab with a cacodemon CACO_TAG + i, its
// glow lights have thing id GLOW_TID + i (map.py).
class CacobeliskObelisks : EventHandler
{
	const SLEEVE_TAG = 100;
	const CACO_TAG = 200;
	const GLOW_TID = 100;
	// Sinking speeds, units a tic. The switch obelisk 0.5 (note #9: the 232 down in about 13 s); the
	// others half that (the mapper, 2026-11-22), about 26 s, so the switch one is the quick one.
	const SINK_SWITCH = 0.5;
	// Note #23: the sleeves stop at the altars' height (map.py: -DROP + 16), not at their base (8 lower),
	// leaving an 8-high rim of the sleeve round each slab.
	const SLEEVE_REST = -240;
	const SINK_OTHERS = 0.25;
	const SLIT_TAG = 400;        // the switch obelisk's slit (map.py SLIT_TAG)
	const SLIT_CONTROL_TAG = 402; // the block of sleeve above the slit's hollow: a 3D floor's control sector (map.py)

	const SHOTGUN_TID = 300;
	const SHOW_DELAY = 175;      // tics from the landing to the first obelisk (5 s; 3 s until 2026-11-24: "a bit more of a delay")
	const SHOW_GAP = 70;         // tics between one obelisk and the next (2 s)
	const HALL_Z = -200;         // a player below this is in the hall (after H, the elevator is up again)

	// Every sleeve in reveal order (pair by pair, west then east), with its pair; the switch obelisk's
	// sleeve apart.
	Array<int> order, orderPair;
	int switchSleeve, switchPair;
	int shown;                   // how many of `order` are revealed
	int showStart;               // maptime of the first; -1 until the elevator lands
	bool switchShown;
	Inventory shotgun;
	bool ready;

	// Mapper, 2026-11-22: the switch obelisk's face is splattered with blood of a colour nothing else
	// bleeds (luminous violet: not human red, not cacodemon blue): UZDoom's own blood splats, sprayed
	// in that colour. A splat is sprayed once the sinking sleeve has passed below it (sprayed earlier,
	// it would land on the sleeve), so each appears as the stone behind it is uncovered.
	// Note #17, "more pronounced": brighter and more saturated (was 0xA030FF), seven marks (was three):
	// the two biggest splats and smears that run down the stone, overlapping across the face.
	const SPLAT_COLOR = 0xFFC020FF;
	static const String SPLAT_DECAL[] = { "BloodSplat1", "BloodSplat2", "BloodSplat1", "BloodSmear",
		"BloodSplat2", "BloodSmear", "BloodSplat1" };
	static const double SPLAT_ALONG[] = { -16, 4, 18, -6, 12, 8, -12 };    // along the face from its middle
	static const double SPLAT_UP[] = { 100, 92, 74, 66, 50, 36, 30 };     // above the base
	Array<double> splatX, splatY, splatZ, splatAngle;
	Array<int> splatSleeve, splatKind;

	// Note #13: the sleeves sink silently (map.py: silent); instead each plays a low, quiet rumble
	// (UZDoom's world/quake, pitched down) while it moves, fading out over a second when it stops.
	const RUMBLE_VOLUME = 0.5;     // note #23 (was 0.33; 0.06 was inaudible, then 0.2)
	const RUMBLE_REACH = 0.5;      // attenuation: half the normal falloff, so it carries about twice as far
	const RUMBLE_PITCH = 0.5;                      // an octave down, half speed (was 0.75)
	const RUMBLE_FADE = 35;                         // tics
	Array<Actor> rumbles;
	Array<int> rumbleSleeve, rumbleFade;
	Array<double> rumbleLastZ;

	// Whether sleeve sector `sleeve` is round the slab tagged CACO_TAG + pair (the switch obelisk).
	bool IsSwitchSleeve(int sleeve, int pair)
	{
		let it = Level.CreateSectorTagIterator(CACO_TAG + pair);
		int s;
		while ((s = it.Next()) >= 0)
		{
			if ((Level.Sectors[sleeve].centerspot - Level.Sectors[s].centerspot).Length() < 40)
				return true;
		}
		return false;
	}

	void FindObelisks()
	{
		switchSleeve = -1;
		showStart = -1;
		int pairs = 0;
		for (int i = 0; i < 64; i++)
		{
			Array<int> sl;
			let it = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
			int s;
			while ((s = it.Next()) >= 0)
			{
				int k = 0;                              // kept sorted west to east
				while (k < sl.Size() && Level.Sectors[sl[k]].centerspot.x < Level.Sectors[s].centerspot.x)
					k++;
				sl.Insert(k, s);
			}
			if (sl.Size() == 0)
				break;
			pairs++;
			for (int k = 0; k < sl.Size(); k++)
			{
				if (IsSwitchSleeve(sl[k], i))
				{
					switchSleeve = sl[k];
					switchPair = i;
					continue;
				}
				order.Push(sl[k]);
				orderPair.Push(i);
			}
			Hum(i);
		}
		shotgun = Inventory(Level.CreateActorIterator(SHOTGUN_TID).Next());
		Console.Printf("[DMS] CacobeliskObelisks: %d pair(s), %d obelisk(s) in the show; switch obelisk %s, shotgun %s",
			pairs, order.Size(), switchSleeve >= 0 ? "found" : "missing", shotgun != null ? "found" : "missing");
	}

	// Note #109: each altar has a snuffed torch (thing id ALTAR_TORCH_TID; CacobeliskTorches makes it the
	// unlit torch). As its obelisk is revealed it flares to life: green, the switch obelisk's violet.
	const ALTAR_TORCH_TID = 321;
	const ALTAR_TORCH_REACH = 120;   // from the obelisk's middle to its altar's torch

	void LightAltarTorch(Vector2 obelisk, bool violet)
	{
		let found = Level.CreateActorIterator(ALTAR_TORCH_TID);
		Actor a, best = null;
		while (a = found.Next())
		{
			if (a is "CacobeliskDeadTorch" && (best == null || (a.pos.xy - obelisk).Length() < (best.pos.xy - obelisk).Length()))
				best = a;
		}
		if (best == null || (best.pos.xy - obelisk).Length() > ALTAR_TORCH_REACH)
			return;
		Vector3 where = best.pos;
		best.Destroy();
		let lit = Actor.Spawn(violet ? "CacobeliskVioletTorch" : "ShortGreenTorch", where, NO_REPLACE);
		if (lit)
		{
			lit.bSolid = false;                      // on an altar, among pickups
			lit.A_StartSound("vile/firestrt", CHAN_BODY, 0, 0.5, ATTN_NORM);
		}
	}

	// Note #116: when the switch obelisk wakes, the sky turns from dark green to a dark red-violet, in two
	// steps a second apart (the map's own sky textures, textures.txt).
	const SKY_DELAY = 35;
	int skyStage, skyAt;

	void SkyShift()
	{
		if (skyStage == 0 || Level.maptime < skyAt)
			return;
		TextureID next = TexMan.CheckForTexture(skyStage == 1 ? "CACOSKY1" : "CACOSKY2", TexMan.Type_Any);
		if (next.IsValid())
			Level.ChangeSky(next, next);
		Console.Printf("[DMS] CacobeliskObelisks: the sky turns (step %d)", skyStage);
		skyStage = skyStage == 1 ? 2 : 0;
		skyAt = Level.maptime + SKY_DELAY;
	}

	// Note #117: once the block above the slit's hollow has sunk to nothing (its top down on its underside),
	// its two faces still showed as a plate floating over the leak. So it is dropped out of sight, under
	// the floor: both its planes go down, fast.
	const SLIT_HIDE = 64;
	bool slitSinking;

	void HideSlitBlock()
	{
		if (!slitSinking)
			return;
		let blocks = Level.CreateSectorTagIterator(SLIT_CONTROL_TAG);
		int k;
		while ((k = blocks.Next()) >= 0)
		{
			Sector block = Level.Sectors[k];
			if (block.ceilingplane.ZAtPoint(block.centerspot) - block.floorplane.ZAtPoint(block.centerspot) > 0.01)
				return;                                  // still coming down
			Level.CreateFloor(block, Floor.floorLowerByValue, null, 64, SLIT_HIDE);
			Level.CreateCeiling(block, Ceiling.ceilLowerByValue, null, 64, 64, SLIT_HIDE);
		}
		slitSinking = false;
	}

	// Note #118: the switch obelisk's later steps, ready for whatever will set them off (nothing does yet).
	Vector2 switchAt;            // the switch obelisk's middle and pair, kept from its reveal
	int switchPairNow;
	bool step2Done, step3Done;

	// Step 2: its altar's torch flares up violet, and the violet paint shows on its face.
	void SwitchObeliskStep2()
	{
		if (!switchShown || step2Done)
			return;
		step2Done = true;
		LightAltarTorch(switchAt, true);
		QueueSplats(switchPairNow);
		Console.Printf("[DMS] CacobeliskObelisks: the switch obelisk, step 2 (torch and paint)");
	}

	// Step 3: the sky begins to turn (note #116); what the obelisk then does is still to be decided.
	void SwitchObeliskStep3()
	{
		if (!step2Done || step3Done)
			return;
		step3Done = true;
		skyStage = 1;
		skyAt = Level.maptime + SKY_DELAY;
		Console.Printf("[DMS] CacobeliskObelisks: the switch obelisk, step 3 (the sky turns)");
	}

	bool PlayerAtShotgun()
	{
		if (shotgun == null)
			return false;
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo)
				continue;
			let mo = players[i].mo;
			double reach = mo.radius + shotgun.radius + 8;
			if (abs(mo.pos.x - shotgun.pos.x) <= reach && abs(mo.pos.y - shotgun.pos.y) <= reach
				&& abs(mo.pos.z - shotgun.pos.z) <= 64)
				return true;
		}
		return false;
	}

	// Note #11: a low rumble from inside the obelisk with the cacodemon (the one to interact with), from
	// the start: UZDoom's earthquake rumble, looped, very quiet, heard only close by.
	void Hum(int i)
	{
		let it = Level.CreateSectorTagIterator(CACO_TAG + i);
		int s;
		while ((s = it.Next()) >= 0)
		{
			Sector slab = Level.Sectors[s];
			Vector2 c = slab.centerspot;
			Actor spot = Actor.Spawn("MapSpot", (c.x, c.y, slab.floorplane.ZAtPoint(c) - 40));
			if (spot != null)
				spot.A_StartSound("world/quake", CHAN_BODY, CHANF_LOOPING, 0.3, ATTN_STATIC);
		}
	}

	override void WorldTick()
	{
		if (!ready)
		{
			ready = true;
			FindObelisks();
		}
		PlayerPawn p = players[consoleplayer].mo;
		if (p == null)
			return;
		// The show starts once the player is down at the bottom (the mapper, 2026-11-22: they can press
		// the switch and step back, letting the platform go down without them; then it waits until they
		// drop down the shaft). Riding it, that's when it lands; after H (the player put back in the
		// hall, the platform up again), straight away.
		if (showStart < 0 && p.pos.z < HALL_Z)
		{
			let el = CacobeliskElevator(EventHandler.Find("CacobeliskElevator"));
			if (el == null || el.broken || !el.riding)
				showStart = Level.maptime + SHOW_DELAY;
		}
		while (showStart >= 0 && shown < order.Size() && Level.maptime >= showStart + shown * SHOW_GAP)
		{
			Reveal(order[shown], orderPair[shown], false, p);
			shown++;
		}
		// The switch obelisk: once the shotgun is taken (it has an owner, or it's gone).
		SkyShift();
		HideSlitBlock();
		// Note #102: or once a player is near enough to take it: with a shotgun and full shells already, it
		// isn't picked up, and the obelisk never woke.
		if (!switchShown && switchSleeve >= 0 && (shotgun == null || shotgun.Owner != null || PlayerAtShotgun()))
		{
			switchShown = true;
			Reveal(switchSleeve, switchPair, true, p);
		}
		SpraySplats();
		UpdateRumbles();
	}

	// Note #21: as a pillar comes to rest, a loud, deep "whumph": the blazing door's slam and the lift's
	// stopping clunk, both pitched well down, from where it landed. Played from a spot of its own that
	// stays, so the sound isn't cut when the rumble's spot goes.
	void Thud(Actor at)
	{
		if (at == null)
			return;
		Actor spot = Actor.Spawn("MapSpot", at.pos);
		if (spot == null)
			return;
		spot.A_StartSound("doors/dr2_clos", CHAN_5, 0, 1.0, ATTN_NORM, 0.55);
		spot.A_StartSound("plats/pt1_stop", CHAN_6, 0, 0.8, ATTN_NORM, 0.5);
	}

	// Each rumble plays while its sleeve moves; once the floor stops, it fades out and goes.
	void UpdateRumbles()
	{
		for (int k = rumbles.Size() - 1; k >= 0; k--)
		{
			Actor r = rumbles[k];
			Sector sleeve = Level.Sectors[rumbleSleeve[k]];
			double z = sleeve.floorplane.ZAtPoint(sleeve.centerspot);
			if (rumbleFade[k] < 0)
			{
				if (z != rumbleLastZ[k])
				{
					rumbleLastZ[k] = z;
					continue;                       // still sinking
				}
				rumbleFade[k] = RUMBLE_FADE;
				Thud(r);
			}
			rumbleFade[k]--;
			if (r != null && rumbleFade[k] > 0)
			{
				r.A_SoundVolume(CHAN_BODY, RUMBLE_VOLUME * rumbleFade[k] / RUMBLE_FADE);
				continue;
			}
			if (r != null)
			{
				r.A_StopSound(CHAN_BODY);
				r.Destroy();
			}
			rumbles.Delete(k);
			rumbleSleeve.Delete(k);
			rumbleFade.Delete(k);
			rumbleLastZ.Delete(k);
		}
	}

	// The splats for pair i's switch obelisk (its slab is tagged CACO_TAG + i): spots 12 out from the
	// face (the side towards the hall's middle, x 32), each to spray once its sleeve is below it.
	void QueueSplats(int i)
	{
		let it = Level.CreateSectorTagIterator(CACO_TAG + i);
		int s;
		while ((s = it.Next()) >= 0)
		{
			Sector slab = Level.Sectors[s];
			Vector2 c = slab.centerspot;
			double dir = c.x < 32 ? 1 : -1;               // from the slab towards the aisle
			double faceX = c.x + dir * 16;
			double baseZ = slab.floorplane.ZAtPoint(c) - 128;
			let sleeves = Level.CreateSectorTagIterator(SLEEVE_TAG + i);
			int sl, sleeve = -1;
			while ((sl = sleeves.Next()) >= 0)            // the sleeve round this slab: the nearest one
			{
				if (sleeve < 0 || (Level.Sectors[sl].centerspot - c).Length() < (Level.Sectors[sleeve].centerspot - c).Length())
					sleeve = sl;
			}
			for (int k = 0; k < SPLAT_UP.Size(); k++)
			{
				splatX.Push(faceX + dir * 12);
				splatY.Push(c.y + SPLAT_ALONG[k]);
				splatZ.Push(baseZ + SPLAT_UP[k]);
				splatAngle.Push(dir > 0 ? 180 : 0);
				splatSleeve.Push(sleeve);
				splatKind.Push(k);
			}
		}
	}

	void SpraySplats()
	{
		for (int k = splatX.Size() - 1; k >= 0; k--)
		{
			Sector sleeve = Level.Sectors[splatSleeve[k]];
			if (sleeve.floorplane.ZAtPoint(sleeve.centerspot) > splatZ[k] - 12)   // the sleeve now rests 8 up
				continue;                                  // still covered
			Actor spot = Actor.Spawn("MapSpot", (splatX[k], splatY[k], splatZ[k]));
			if (spot != null)
			{
				spot.angle = splatAngle[k];
				spot.A_SprayDecal(SPLAT_DECAL[splatKind[k]], 32, (0, 0, 0), (0, 0, 0), false, SPLAT_COLOR);
				spot.Destroy();
			}
			splatX.Delete(k);
			splatY.Delete(k);
			splatZ.Delete(k);
			splatAngle.Delete(k);
			splatSleeve.Delete(k);
			splatKind.Delete(k);
		}
	}

	// Reveals one obelisk: its sleeve (sector `sleeve`, of pair `pair`) sinks, its rumble and clack
	// start, its glow comes on; the switch obelisk also gets its cacodemon and its violet splats.
	void Reveal(int sleeve, int pair, bool isSwitch, Actor player)
	{
		Sector sec = Level.Sectors[sleeve];
		Vector2 sc = sec.centerspot;
		double drop = sec.floorplane.ZAtPoint(sc) - SLEEVE_REST;
		Level.CreateFloor(sec, Floor.floorLowerByValue, null, isSwitch ? SINK_SWITCH : SINK_OTHERS, drop);
		// Note #118 (2026-11-24): the switch obelisk goes in three steps. Step 1 is this reveal (the shotgun): its
		// sleeve sinks, its cacodemon and its leak appear, and no more: its torch stays out, no paint, no
		// change in the sky. Step 2 (a switch, to come) is SwitchObeliskStep2: the torch and the paint. Step 3
		// (an item placed in a niche, to come) is SwitchObeliskStep3: the sky turns, and what follows.
		if (!isSwitch)
			LightAltarTorch(sc, false);
		else
		{
			switchAt = sc;
			switchPairNow = pair;
		}
		if (isSwitch)
		{
			// Note #38: the slit the violet spills from (a hollow low in the sleeve's back). Note #107: the
			// piece of sleeve above the hollow is a 3D floor (its control sector tagged SLIT_CONTROL_TAG): its
			// top comes down with the sinking sleeve, at the same speed, until it meets its underside and
			// nothing of it is left.
			let blocks = Level.CreateSectorTagIterator(SLIT_CONTROL_TAG);
			int k;
			while ((k = blocks.Next()) >= 0)
			{
				Sector block = Level.Sectors[k];
				double thick = block.ceilingplane.ZAtPoint(block.centerspot) - block.floorplane.ZAtPoint(block.centerspot);
				if (thick > 0)
					Level.CreateCeiling(block, Ceiling.ceilLowerByValue, null, SINK_SWITCH, SINK_SWITCH, thick);
			}
			slitSinking = true;
		}
		int cacos = 0;
		if (isSwitch)
		{
			let it = Level.CreateSectorTagIterator(CACO_TAG + pair);
			int s;
			while ((s = it.Next()) >= 0)
			{
				Sector slab = Level.Sectors[s];
				Vector2 c = slab.centerspot;
				Actor caco = Actor.Spawn("CacobeliskDozer", (c.x, c.y, slab.floorplane.ZAtPoint(c)), NO_REPLACE);
				if (caco != null)
				{
					caco.angle = caco.AngleTo(player);
					// A dark cacodemon (the mapper, 2026-11-22): a dark, mostly see-through silhouette.
					caco.A_SetRenderStyle(1.0, STYLE_Shadow);
					cacos++;
				}
			}
		}
		Actor r = Actor.Spawn("MapSpot", (sc.x, sc.y, player.pos.z + 48));
		if (r != null)
		{
			r.A_StartSound("world/quake", CHAN_BODY, CHANF_LOOPING, RUMBLE_VOLUME, RUMBLE_REACH, RUMBLE_PITCH);
			// Note #23: a sharp clack as it starts: the switch click, pitched a little down, over the
			// lift's starting clunk.
			r.A_StartSound("switches/normbutn", CHAN_5, 0, 1.0, ATTN_NORM, 0.75);   // 75% speed (the mapper)
			r.A_StartSound("plats/pt1_strt", CHAN_6, 0, 0.7, ATTN_NORM, 0.75);
			rumbles.Push(r);
			rumbleSleeve.Push(sleeve);
			rumbleFade.Push(-1);
			rumbleLastZ.Push(1e9);           // "moving": the floor only starts on the next tic
		}
		// Its glow: of the pair's lights (GLOW_TID + pair), the one in front of this obelisk.
		let lights = Level.CreateActorIterator(GLOW_TID + pair);
		Actor l;
		while ((l = lights.Next()) != null)
		{
			if ((l.pos.xy - sc).Length() < 100)
				l.Activate(null);
		}
		Console.Printf("[DMS] CacobeliskObelisks: pair %d, %s obelisk revealed%s", pair + 1,
			sc.x < 32 ? "west" : "east", cacos > 0 ? " (with its cacodemon)" : "");
	}
}

// Note #11 (2026-11-23): the cistern's spectres are asleep: they neither hear nor see the player, and
// wake only when touched or hurt, so a careful player can skirt round them. A spectre whose idle state
// never looks (no A_Look); being hurt wakes any monster by itself, and Tick wakes it on a touch. The
// handler swaps the map's spectres (thing id SLEEPER_TID, map.py) for it when the level loads.
class CacobeliskSleeper : Spectre
{
	const TOUCH = 8;             // how near (beyond the two radii) counts as a touch

	States
	{
	Spawn:
		SARG AB 10;
		Loop;
	}

	override void Tick()
	{
		Super.Tick();
		if (health <= 0 || target || !InStateSequence(CurState, SpawnState))
			return;
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo)
				continue;
			let mo = players[i].mo;
			if (mo.health > 0 && Distance2D(mo) <= radius + mo.radius + TOUCH
				&& mo.pos.z < pos.z + height && pos.z < mo.pos.z + mo.height)
			{
				target = mo;
				A_StartSound(SeeSound, CHAN_VOICE);
				SetState(SeeState);
				Console.Printf("[DMS] CacobeliskSleeper: a spectre was touched and woke");
				return;
			}
		}
	}
}

class CacobeliskSleepers : EventHandler
{
	const SLEEPER_TID = 310;     // the cistern's spectres (map.py SLEEPER_TID)

	override void WorldLoaded(WorldEvent e)
	{
		Array<Actor> found;
		let it = Level.CreateActorIterator(SLEEPER_TID);
		Actor a;
		while (a = it.Next())
			if (!(a is "CacobeliskSleeper"))
				found.Push(a);
		for (int i = 0; i < found.Size(); i++)
		{
			let old = found[i];
			let s = Actor.Spawn("CacobeliskSleeper", old.pos, NO_REPLACE);
			if (!s)
				continue;
			s.angle = old.angle;
			old.ClearCounters();
			old.Destroy();
		}
		Console.Printf("[DMS] CacobeliskSleepers: %d spectre(s) asleep", found.Size());
	}
}

// Note #12 (2026-11-23): the switch obelisk's cacodemon is asleep too: a shadow minding its own business
// up there. Note #32: deaf to gunshots as well (at first it woke on hearing the player), like the
// cistern's spectres: it never looks or listens, and wakes only when hurt (as any monster does) or when a
// player touches it.
class CacobeliskDozer : Cacodemon
{
	const REACH = 8;             // how near (beyond the two radii) counts as a touch

	States
	{
	Spawn:
		HEAD A 10;
		Loop;
	}

	override void Tick()
	{
		Super.Tick();
		if (health <= 0 || target || !InStateSequence(CurState, SpawnState))
			return;
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo)
				continue;
			let mo = players[i].mo;
			if (mo.health > 0 && Distance2D(mo) <= radius + mo.radius + REACH
				&& mo.pos.z < pos.z + height && pos.z < mo.pos.z + mo.height)
			{
				target = mo;
				A_StartSound(SeeSound, CHAN_VOICE);
				SetState(SeeState);
				Console.Printf("[DMS] CacobeliskDozer: the cacodemon was touched and woke");
				return;
			}
		}
	}
}

// Note #18 (2026-11-23): which way the water runs. It flows away from the obelisk hall, slow and lazy:
// the west gutter and its drain west, the east gutter and its drain east, the cistern's on east and out
// under its east wall. Using the switch on the cistern's dais turns the cistern's water south and speeds
// it up a little. Only the water's picture moves (its floor's texture offset, a little each tic); the
// player isn't carried. Sectors are found by tag (map.py FLOW_WEST_TAG, FLOW_EAST_TAG, CISTERN_TAG).
class CacobeliskWater : EventHandler
{
	const WEST_TAG = 610;
	const EAST_TAG = 611;
	const CISTERN_TAG = 600;
	const SWITCH_TAG = 601;      // the dais and its post: lit a little when the switch is used
	const DAIS_LIGHT = 96;
	const BIG_DOOR_TAG = 7;      // the big door on the stairs (map.py CISTERN_DOOR_TAG)
	const DOOR_GLOW_TID = 303;   // the red light behind it (map.py CISTERN_DOOR_GLOW_TID)
	const GUARD_TID = 304;       // the shotgunners who come at once (map.py CISTERN_DOOR_WAKE_TID)
	const ROOM_SWITCH_TAG = 9;   // the switch's twin inside the room behind the door (map.py CISTERN_DOOR_SWITCH_TAG)
	const LAZY = 0.12;           // map units a tic (about 4 a second)
	const SOUTH_SPEED = 0.2;     // the cistern's, once the switch is used (not "TURNED": names ignore case)

	// Note #26: once the switch is used, the cistern's current carries the player too: a push south each
	// tic while they stand in its water (friction settles it at about 11 times this: ~2 units a tic, a
	// quarter of walking speed, so it can be walked against).
	const PUSH_SOUTH = 0.18;

	bool turned;

	// Push everything the current can take, standing on the floor of a sector tagged `tag`, by (dx, dy) a
	// tic: players, and (note #62) monsters and bodies. Not a monster still asleep (the spectres would
	// drift into the player and spoil skirting round them), nor anything that flies.
	void Carry(int tag, double dx, double dy)
	{
		let it = Level.CreateSectorTagIterator(tag);
		int i;
		while ((i = it.Next()) >= 0)
		{
			for (Actor a = Level.sectors[i].thinglist; a != null; a = a.snext)
			{
				if (a.pos.z > a.floorz || a.bNoGravity)
					continue;
				bool body = a.bCorpse || (a.bIsMonster && a.health <= 0);
				bool awake = a.bIsMonster && a.health > 0 && a.target != null;
				if (a.player != null || body || awake)
				{
					a.vel.x += dx;
					a.vel.y += dy;
				}
			}
		}
	}

	// Move the water's picture in every sector tagged `tag` by (dx, dy) map units (east, north). A flat's
	// picture sits at x + its x offset and at -y + its y offset, so east is a smaller x offset and north
	// a bigger y offset.
	void Flow(int tag, double dx, double dy)
	{
		let it = Level.CreateSectorTagIterator(tag);
		int i;
		while ((i = it.Next()) >= 0)
		{
			Sector s = Level.sectors[i];
			if (dx != 0) s.AddXOffset(Sector.floor, -dx);
			if (dy != 0) s.AddYOffset(Sector.floor, dy);
		}
	}

	// Note #52: trying the big door by hand, while it's still shut, says it opens elsewhere: a player who
	// presses use within reach of it and facing it gets the message and the "can't use that" grunt. (The
	// door's lines have no special of their own to hang a message on: the switch opens it.)
	const DOOR_REACH = 100;      // from the door's middle (it is 112 wide, 16 thick)
	const DOOR_FACING = 55;      // degrees either side

	void TryBigDoor()
	{
		if (turned)
			return;
		let doors = Level.CreateSectorTagIterator(BIG_DOOR_TAG);
		int di = doors.Next();
		if (di < 0)
			return;
		Vector2 c = Level.sectors[di].centerspot;
		for (int p = 0; p < MAXPLAYERS; p++)
		{
			if (!playeringame[p] || !players[p].mo)
				continue;
			if (!(players[p].cmd.buttons & BT_USE) || (players[p].oldbuttons & BT_USE))
				continue;
			let mo = players[p].mo;
			Vector2 d = c - mo.pos.xy;
			if (d.Length() <= DOOR_REACH && abs(Actor.deltaangle(mo.angle, VectorAngle(d.x, d.y))) <= DOOR_FACING)
			{
				mo.A_Print("This door is opened elsewhere.");
			}
		}
	}

	override void WorldTick()
	{
		TryBigDoor();
		Flow(WEST_TAG, -LAZY, 0);
		Flow(EAST_TAG, LAZY, 0);
		if (turned)
		{
			Flow(CISTERN_TAG, 0, -SOUTH_SPEED);
			Carry(CISTERN_TAG, 0, -PUSH_SOUTH);
		}
		else
			Flow(CISTERN_TAG, LAZY, 0);
	}

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		// The dais switch: its own special is the big door on the stairs (Door_Open, note #41); the rest
		// happens here: the dais lights up, the water turns, and the red glow behind the door comes on.
		if (ln != null && !turned && ln.special == Door_Open && ln.args[0] == BIG_DOOR_TAG)
		{
			turned = true;
			Level.ExecuteSpecial(Light_ChangeToValue, null, null, false, SWITCH_TAG, DAIS_LIGHT);
			// Note #87: the twin switch inside the room behind the door is for one use: whichever of the two
			// was used, its post snaps into the floor (its top is the room's rock: nothing is left to see).
			Level.ExecuteSpecial(Floor_LowerToLowest, null, null, false, ROOM_SWITCH_TAG, 64);
			// Note #90: the two switches are one: whichever was used, the other shows as flipped (SW2WOOD) and
			// does nothing more, so the door can't be "opened" a second time from the other side.
			TextureID swOff = TexMan.CheckForTexture("SW1WOOD", TexMan.Type_Wall);
			TextureID swOn = TexMan.CheckForTexture("SW2WOOD", TexMan.Type_Wall);
			for (int i = 0; i < Level.Lines.Size(); i++)
			{
				Line other = Level.Lines[i];
				if (other == ln || other.special != Door_Open || other.args[0] != BIG_DOOR_TAG)
					continue;
				other.special = 0;
				for (int sn = 0; sn < 2; sn++)
				{
					Side sd = other.sidedef[sn];
					if (sd == null)
						continue;
					for (int part = Side.top; part <= Side.bottom; part++)
					{
						if (sd.GetTexture(part) == swOff)
							sd.SetTexture(part, swOn);
					}
				}
			}
			// Note #48: two of the shotgunners behind the door come for whoever used the switch at once.
			let guards = Level.CreateActorIterator(GUARD_TID);
			Actor guard;
			int roused = 0;
			while ((guard = guards.Next()) != null)
			{
				if (guard.health > 0 && e.Thing != null)
				{
					guard.target = e.Thing;
					guard.SetState(guard.SeeState);
					roused++;
				}
			}
			Console.Printf("[DMS] CacobeliskWater: %d guard(s) roused behind the big door", roused);
			let glows = Level.CreateActorIterator(DOOR_GLOW_TID);
			Actor glow;
			while ((glow = glows.Next()) != null)
				glow.Activate(null);
			Console.Printf("[DMS] CacobeliskWater: the switch was used; the cistern's water turns south");
		}
	}
}

// Note #39 (2026-11-23): dust from the secret panel: the bullet puff's smoke, bigger, pale and see-through,
// drifting where it is thrown, slowing and fading out over about two seconds.
// Note #90 (2026-11-26): the main passage's secret wall (map.py PASSAGE_SECRET) spits out a little puff of
// dust as it starts to lift, out of its foot into the passage, like the start's secret panel (note #39).
class CacobeliskPassageSecret : EventHandler
{
	const DOOR_TAG = 10;        // map.py PASSAGE_SECRET_TAG
	const PUFFS = 8;

	const SHORTCUT_TAG = 12;    // map.py STORE_SHORTCUT_TAG: the storage room's shortcut box
	const SHUTTER_TAG = 15;     // map.py STORE_SWITCH_SHUTTER_TAG: the panel in front of its switch

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		// Note #149 (2026-11-26): the shortcut's switch is one use: a panel snaps down over it, as at the elevator.
		if (ln != null && ln.special == Floor_LowerByValue && ln.args[0] == SHORTCUT_TAG)
		{
			Level.ExecuteSpecial(Ceiling_LowerByValue, null, null, false, SHUTTER_TAG, 64, 32);
			Console.Printf("[DMS] CacobeliskPassageSecret: the shortcut opens; its switch is shut away");
			return;
		}
		if (ln == null || ln.special != Door_Open || ln.args[0] != DOOR_TAG)
			return;
		Vector2 mid = ln.v1.p + ln.delta / 2;
		Vector2 outw = (ln.delta.y, -ln.delta.x).Unit();     // the front side's way: into the passage
		Vector2 along = ln.delta.Unit();
		double z0 = ln.frontsector.floorplane.ZAtPoint(mid);
		for (int n = 0; n < PUFFS; n++)
		{
			Vector2 spot = mid + outw * 6 + along * FRandom(-18, 18);
			Actor puff = Actor.Spawn("CacobeliskDust", (spot.x, spot.y, z0 + FRandom(2, 20)), NO_REPLACE);
			if (puff != null)
			{
				Vector2 v = outw * FRandom(0.3, 1.0) + along * FRandom(-0.3, 0.3);
				puff.vel = (v.x, v.y, FRandom(0.02, 0.2));
			}
		}
		Console.Printf("[DMS] CacobeliskPassageSecret: the wall lifts");
	}
}

class CacobeliskDust : Actor
{
	Default
	{
		+NOGRAVITY
		+NOBLOCKMAP
		+NOINTERACTION
		RenderStyle "Translucent";
		Alpha 0.45;
		Scale 1.6;
	}

	States
	{
	Spawn:
		PUFF CCDD 9 A_FadeOut(0.05);
		PUFF D 4 A_FadeOut(0.06);
		Wait;
	}

	override void Tick()
	{
		Super.Tick();
		vel *= 0.96;
	}
}

// Chat, 2026-11-24: unlit torches. The game has none, so the map makes one from the short red torch's
// sprite (textures.txt): its bowl and stem, darkened and not full bright, with the flame's own frames in
// grey, see-through, as smoke over it. No light. The handler swaps the map's torches with thing id
// DEAD_TID (map.py DEAD_TORCH_TID) for it when the level loads.
// The skull's eyes are a dim, still purple (in the sprite); the torch is snuffed and gives no light at all.
class CacobeliskDeadTorch : Actor
{
	Actor smoke;

	Default
	{
		Radius 16;
		Height 28;
		ProjectilePassHeight -16;
		+SOLID
	}

	States
	{
	Spawn:
		CACT A -1;
		Stop;
	}

	override void PostBeginPlay()
	{
		Super.PostBeginPlay();
		smoke = Actor.Spawn("CacobeliskTorchSmoke", pos + (0, 0, 28), NO_REPLACE);
	}

	override void OnDestroy()
	{
		if (smoke)
			smoke.Destroy();
		Super.OnDestroy();
	}
}

class CacobeliskTorchSmoke : Actor
{
	Default
	{
		+NOGRAVITY
		+NOBLOCKMAP
		+NOINTERACTION
		RenderStyle "Translucent";
		Alpha 0.35;
	}

	States
	{
	Spawn:
		CACS ABCD 7;
		Loop;
	}
}

class CacobeliskTorches : EventHandler
{
	const DEAD_TID = 320;
	const ALTAR_TID = 321;       // the altars' torches (note #109): unlit too, not solid, lit by CacobeliskObelisks
	// Note #95 (2026-11-24): when the big door on the stairs is opened (either of its switches), the dead
	// torches flare up one after another, from the cistern's south end back up to the stairs: each becomes
	// a burning torch (with its light), with a whoosh, and its hollow brightens.
	const BIG_DOOR_TAG = 7;      // map.py CISTERN_DOOR_TAG
	const FLARE_START = 35;      // tics after the switch
	const FLARE_GAP = 35;        // between one torch and the next
	const HOLLOW_GLOW = 64;      // added to the hollow's light

	Array<Actor> waiting;
	int flareAt;
	bool flaring;

	override void WorldLoaded(WorldEvent e)
	{
		Array<Actor> found;
		let it = Level.CreateActorIterator(DEAD_TID);
		Actor a;
		while (a = it.Next())
			if (!(a is "CacobeliskDeadTorch"))
				found.Push(a);
		for (int i = 0; i < found.Size(); i++)
		{
			let old = found[i];
			let t = Actor.Spawn("CacobeliskDeadTorch", old.pos, NO_REPLACE);
			if (t)
				old.Destroy();
		}
		// The altars' torches: the same unlit torch, but not solid (pickups lie round it), and it keeps
		// its thing id so the obelisks' handler finds it.
		Array<Actor> onAltars;
		let alt = Level.CreateActorIterator(ALTAR_TID);
		while (a = alt.Next())
			if (!(a is "CacobeliskDeadTorch"))
				onAltars.Push(a);
		for (int i = 0; i < onAltars.Size(); i++)
		{
			let old = onAltars[i];
			let t = Actor.Spawn("CacobeliskDeadTorch", old.pos, NO_REPLACE);
			if (!t)
				continue;
			t.bSolid = false;
			t.ChangeTid(ALTAR_TID);
			old.Destroy();
		}
		Console.Printf("[DMS] CacobeliskTorches: %d torch(es) unlit, %d on altars", found.Size(), onAltars.Size());
	}

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		if (flaring || ln == null || ln.special != Door_Open || ln.args[0] != BIG_DOOR_TAG)
			return;
		flaring = true;
		// South to north: up the cistern, then up the stairs.
		let it = ThinkerIterator.Create("CacobeliskDeadTorch");
		Actor a;
		while (a = Actor(it.Next()))
		{
			if (a.tid == ALTAR_TID)                  // the altars' torches are the obelisks' to light
				continue;
			int at = 0;
			while (at < waiting.Size() && waiting[at].pos.y <= a.pos.y)
				at++;
			waiting.Insert(at, a);
		}
		flareAt = Level.maptime + FLARE_START;
		Console.Printf("[DMS] CacobeliskTorches: the big door opens; %d torch(es) will flare up", waiting.Size());
	}

	override void WorldTick()
	{
		if (!flaring || waiting.Size() == 0 || Level.maptime < flareAt)
			return;
		Actor old = waiting[0];
		waiting.Delete(0);
		flareAt = Level.maptime + FLARE_GAP;
		if (!old)
			return;
		Vector3 where = old.pos;
		Sector hollow = old.CurSector;
		old.Destroy();
		let lit = Actor.Spawn("ShortRedTorch", where, NO_REPLACE);
		if (lit)
			lit.A_StartSound("vile/firestrt", CHAN_BODY, 0, 0.6, ATTN_NORM);
		if (hollow)
			hollow.SetLightLevel(min(255, hollow.lightlevel + HOLLOW_GLOW));
	}
}

// Note #109: the switch obelisk's altar torch burns violet (the map's own sprite, textures.txt CACP: the blue
// and the red torch's flames mixed), with a violet light.
class CacobeliskVioletTorch : Actor
{
	Default
	{
		Radius 16;
		Height 37;
		ProjectilePassHeight -16;
	}

	States
	{
	Spawn:
		CACP ABCD 4 Bright;
		Loop;
	}

	override void PostBeginPlay()
	{
		Super.PostBeginPlay();
		A_AttachLight('CacobeliskViolet', DynamicLight.RandomFlickerLight, Color(170, 60, 255), 48, 60, DYNAMICLIGHT.LF_ATTENUATE, (0, 0, 40), 0.2);
	}
}

// 2026-11-26 (chat): the station's drones, the lost soul gone machine. The mapper wanted a variant of the lost soul,
// human/robot instead of bio/alien, that doesn't charge: it stares for a moment, then fires. Then (same day) two
// kinds: the cyan drone (CacobeliskDrone: frail, a fan of three small fast bolts, one at the player and one
// either side) and the stronger red one (CacobeliskRedDrone: two shotgun blasts to kill, two bigger, slower,
// harder bolts, both on target). Their sprites are the map's own (sprites/CBDC*, CBDR*, bolts CBBC*, CBBL*;
// drawn by art/drone_sprites.py after Freedoom's chaingunner and revenant). map.py places lost souls with
// DRONE_TID or RED_DRONE_TID; CacobeliskDrones swaps them when the level loads, so the editor and the movement
// check see a lost soul there.
class CacobeliskDrone : Actor
{
	const STARE_TICS = 4;        // each look while it stares; eight of them, a little under a second
	const SPREAD = 7;            // degrees between the cyan drone's bolts

	Default
	{
		Monster;
		+FLOAT
		+NOGRAVITY
		+NOBLOOD                 // a machine: bullets strike sparks
		+DONTFALL
		Health 25;               // two or three pistol or chaingun bullets (5, 10 or 15 each)
		Radius 14;
		Height 40;
		Mass 50;
		Speed 8;
		PainChance 160;
		MinMissileChance 160;    // fires a little more readily than most (200 is the usual)
		SeeSound "baby/sight";
		ActiveSound "cacobelisk/drone/active";   // 2026-11-27: the sputter of static (sndinfo.txt)
		PainSound "cacobelisk/drone/pain";       // the crunch of static (sndinfo.txt), not a groan
		DeathSound "cacobelisk/drone/death";     // the squelch of static, then a small explosion (Death)
		Obituary "%o was picked off by a station drone.";
		DropItem "Cell";         // 2026-11-27 (chat): every drone drops a small energy cell (a dropped one gives half: 10)
		Tag "Station drone";
	}

	// One look while it stares: turn to the player, and give up (back to chasing) if they're gone from sight.
	state DroneStare()
	{
		A_FaceTarget();
		if (!target || target.health <= 0 || !CheckSight(target))
			return ResolveState("See");
		return ResolveState(null);
	}

	States
	{
	Spawn:
		CBDC AB 8 A_Look;
		Loop;
	See:
		CBDC AABB 3 A_Chase;
		Loop;
	Missile:
		// It stops, turns to the player and stares, its visor charging, then fans out three bolts.
		CBDC C 0 A_StartSound("misc/chat", CHAN_VOICE);
		CBDC CDCDCDCD STARE_TICS { return DroneStare(); }
		// Note #164 (2026-11-26): the three bolts one after another (pew, pew, pew), not all at once.
		// Mapper, 2026-11-26: one of three volleys, at random: 40% the fan swept left to right, 40% right to left
		// (both aimed where it stared, no turning between shots), 20% all three straight at the player, turning
		// to follow them before each shot.
		CBDC D 0
		{
			int r = Random(0, 99);
			if (r < 40)
				return ResolveState("VolleyLeftRight");
			if (r < 80)
				return ResolveState("VolleyRightLeft");
			return ResolveState("VolleyAimed");
		}
	VolleyLeftRight:
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20, 0, SPREAD);     // + is to its left
		CBDC D 3;
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20);
		CBDC D 3;
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20, 0, -SPREAD);
		CBDC D 6;
		Goto See;
	VolleyRightLeft:
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20, 0, -SPREAD);
		CBDC D 3;
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20);
		CBDC D 3;
		CBDC E 3 Bright A_SpawnProjectile("CacobeliskDroneBolt", 20, 0, SPREAD);
		CBDC D 6;
		Goto See;
	VolleyAimed:
		CBDC E 3 Bright { A_FaceTarget(); A_SpawnProjectile("CacobeliskDroneBolt", 20); }
		CBDC D 3 A_FaceTarget;
		CBDC E 3 Bright { A_FaceTarget(); A_SpawnProjectile("CacobeliskDroneBolt", 20); }
		CBDC D 3 A_FaceTarget;
		CBDC E 3 Bright { A_FaceTarget(); A_SpawnProjectile("CacobeliskDroneBolt", 20); }
		CBDC D 6;
		Goto See;
	Pain:
		CBDC F 3;
		CBDC F 3 A_StartSound(PainSound, CHAN_VOICE, 0, 1.0, ATTN_NORM, FRandom(0.85, 1.2));   // the static, a little higher or lower each time
		Goto See;
	Death:
		// 2026-11-27 (chat): it hangs there shorting out (the squelch of static, DeathSound), then pops like a
		// lost soul (skull/death, a small explosion).
		CBDC F 10 A_Scream;
	Pop:
		MISL B 8 Bright { A_NoBlocking(); A_StartSound("skull/death", CHAN_BODY); }
		MISL C 6 Bright;
		MISL D 4 Bright;
		Stop;
	}
}

// The red drone: two shotgun blasts to bring down (a blast is 35-105, about 70; one reaches 90 only rarely), and
// two bolts, one after the other, both aimed at the player.
class CacobeliskRedDrone : CacobeliskDrone
{
	Default
	{
		Health 90;
		PainChance 96;           // flinches less than the cyan one
		Obituary "%o was shot down by a red station drone.";
		Tag "Red station drone";
	}

	States
	{
	Spawn:
		CBDR AB 8 A_Look;
		Loop;
	See:
		CBDR AABB 3 A_Chase;
		Loop;
	Missile:
		CBDR C 0 A_StartSound("misc/chat", CHAN_VOICE);
		CBDR CDCDCDCD STARE_TICS { return DroneStare(); }
		CBDR E 4 Bright A_SpawnProjectile("CacobeliskRedDroneBolt", 20);
		CBDR D 8 A_FaceTarget;
		CBDR E 4 Bright A_SpawnProjectile("CacobeliskRedDroneBolt", 20);
		CBDR D 6;
		Goto See;
	Pain:
		CBDR F 3;
		CBDR F 3 A_StartSound(PainSound, CHAN_VOICE, 0, 1.0, ATTN_NORM, FRandom(0.85, 1.2));   // the static, a little higher or lower each time
		Goto See;
	Death:
		CBDR F 10 A_Scream;     // shorting out, then the pop (the cyan drone's Death)
		Goto Pop;
	}
}

// The cyan drone's bolt: small and quick (three times an imp's fireball); it stings rather than hurts: 3 to 6.
class CacobeliskDroneBolt : Actor
{
	Default
	{
		Projectile;
		Radius 4;
		Height 6;
		Speed 30;
		FastSpeed 40;
		DamageFunction (Random(3, 6));
		RenderStyle "Add";
		Alpha 0.9;
		SeeSound "baby/attack";
		DeathSound "baby/shotx";
		Decal "PlasmaScorchLower";
	}

	States
	{
	Spawn:
		CBBC AB 2 Bright;
		Loop;
	Death:
		CBBC CDE 3 Bright;
		Stop;
	}
}

// The red drone's bolt: bigger, slower (twice an imp's fireball), a little harder: 6 to 10.
class CacobeliskRedDroneBolt : CacobeliskDroneBolt
{
	Default
	{
		Radius 6;
		Height 8;
		Speed 20;
		FastSpeed 28;
		DamageFunction (Random(6, 10));
	}

	States
	{
	Spawn:
		CBBL AB 2 Bright;
		Loop;
	Death:
		CBBL CDE 3 Bright;
		Stop;
	}
}

class CacobeliskDrones : EventHandler
{
	const DRONE_TID = 330;       // map.py DRONE_TID: lost souls that are cyan drones
	const RED_DRONE_TID = 331;   // map.py RED_DRONE_TID: ... red drones
	const YELLOW_DRONE_TID = 332;   // map.py YELLOW_DRONE_TID: ... yellow drones
	const GUARD_ZOMBIE_TID = 333;   // map.py GUARD_ZOMBIE_TID: the guard posts' zombiemen (note #174)
	const DRONE_GUN_TID = 334;      // map.py DRONE_GUN_TID: plasma rifles that are drone guns (2026-11-27)

	override void WorldLoaded(WorldEvent e)
	{
		int cyan = Swap(DRONE_TID, "CacobeliskDrone");
		int red = Swap(RED_DRONE_TID, "CacobeliskRedDrone");
		int yellow = Swap(YELLOW_DRONE_TID, "CacobeliskYellowDrone");
		Swap(GUARD_ZOMBIE_TID, "CacobeliskGuardZombie");
		Swap(DRONE_GUN_TID, "CacobeliskDroneGun");
		Console.Printf("[DMS] CacobeliskDrones: %d cyan, %d red and %d yellow drone(s) in the station", cyan, red, yellow);
	}

	int Swap(int tid, class<Actor> kind)
	{
		Array<Actor> found;
		let it = Level.CreateActorIterator(tid);
		Actor a;
		while (a = it.Next())
			if (a.GetClass() != kind)     // not one already swapped in (the yellow one is a lost soul too)
				found.Push(a);
		for (int i = 0; i < found.Size(); i++)
		{
			let old = found[i];
			let d = Actor.Spawn(kind, old.pos, NO_REPLACE);
			if (!d)
				continue;
			d.angle = old.angle;
			d.bAmbush = old.bAmbush;     // note #167: a deaf one (the box room's) stays deaf
			d.ChangeTid(tid);
			old.ClearCounters();
			old.Destroy();
		}
		return found.Size();
	}
}

// Note #153 (2026-11-26): a rune on the great door's small door, on its face to the hall (the line with
// id map.py WICKET_RUNE_LINE): the map's own decal (decaldef.txt CacobeliskRune). Sprayed onto the door's
// face, the upper part of the frame's side, hung from the door's underside, so it rides up as the door opens.
class CacobeliskRunes : EventHandler
{
	const WICKET_RUNE_LINE = 901;
	const RUNE_UP = 38;          // the rune's middle above the door's sill

	override void WorldLoaded(WorldEvent e)
	{
		if (e.IsSaveGame)
			return;              // a saved game keeps its decals
		int n = 0;
		let it = Level.CreateLineIdIterator(WICKET_RUNE_LINE);
		int i;
		while ((i = it.Next()) >= 0)
		{
			Line ln = Level.Lines[i];
			Vector2 d = ln.delta;
			Vector2 normal = (d.y, -d.x) / d.Length();             // towards the front side
			Vector2 mid = ln.v1.p + d / 2;
			Vector2 at = mid + normal * 12;
			double z = ln.frontsector.floorplane.ZAtPoint(mid) + RUNE_UP;
			Actor spot = Actor.Spawn("MapSpot", (at.x, at.y, z));
			if (spot == null)
				continue;
			spot.angle = atan2(-normal.y, -normal.x);
			spot.A_SprayDecal("CacobeliskRune", 32);
			spot.Destroy();
			n++;
		}
		Console.Printf("[DMS] CacobeliskRunes: %d rune(s) on the small door", n);
	}
}

// Note #159 (2026-11-26): the storage room's pincer. All its monsters are deaf (ambush: gunfire elsewhere leaves
// them be), but once any of its imps engages (has a target, or is hurt or dead), the two pinkies wake and
// come for the same player, round either side of the boxes (the middle lane is too narrow for them: map.py
// STORE_BOXES), while the imps come down the middle.
class CacobeliskPincer : EventHandler
{
	const STORE_PINKY_TID = 340;     // map.py STORE_PINKY_TID
	const STORE_IMP_TID = 341;       // map.py STORE_IMP_TID
	bool sprung;

	override void WorldTick()
	{
		if (sprung || Level.maptime % 4)
			return;
		Actor foe = null;
		bool engaged = false;
		let it = Level.CreateActorIterator(STORE_IMP_TID);
		Actor imp;
		while (imp = it.Next())
		{
			if (imp.health <= 0 || imp.health < imp.SpawnHealth() || (imp.target && imp.target.player))
			{
				engaged = true;
				if (imp.target && imp.target.player && imp.target.health > 0)
					foe = imp.target;
			}
		}
		if (!engaged)
			return;
		sprung = true;
		if (!foe)                                    // an imp killed before it saw anyone: the nearest player
		{
			for (int i = 0; i < MAXPLAYERS; i++)
				if (playeringame[i] && players[i].mo && players[i].mo.health > 0)
				{
					foe = players[i].mo;
					break;
				}
		}
		if (!foe)
			return;
		int n = 0;
		let pit = Level.CreateActorIterator(STORE_PINKY_TID);
		Actor pinky;
		while (pinky = pit.Next())
		{
			if (pinky.health <= 0)
				continue;
			n++;
			if (pinky.target && pinky.target.player)
				continue;                            // already after someone
			pinky.target = foe;
			pinky.A_StartSound(pinky.SeeSound, CHAN_VOICE);
			pinky.SetState(pinky.SeeState);
		}
		Console.Printf("[DMS] CacobeliskPincer: the imps engaged; %d pinky(s) come round the boxes", n);
	}
}

// Note #161 (2026-11-26): a player who tries to use the shortcut box from the storage room's side (its face, the
// line with id map.py STORE_SHORTCUT_FACE_LINE) is told "Out of reach for now..." (the game grunts its own
// "can't use that" anyway), until the box has sunk. The face has no special of its own (it would count as a switch for
// the movement check), so the use key is watched here: a press, then a trace as far as the player's use range.
class CacobeliskShortcutHint : EventHandler
{
	const FACE_LINE = 902;       // map.py STORE_SHORTCUT_FACE_LINE
	const SHORTCUT_TAG = 12;     // map.py STORE_SHORTCUT_TAG
	bool held[MAXPLAYERS];
	double boxTop;
	int box, face;

	override void WorldLoaded(WorldEvent e)
	{
		box = Level.CreateSectorTagIterator(SHORTCUT_TAG).Next();
		face = Level.CreateLineIdIterator(FACE_LINE).Next();
		if (box >= 0)
			boxTop = Level.Sectors[box].floorplane.ZAtPoint(Level.Sectors[box].centerspot);
	}

	override void WorldTick()
	{
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo)
				continue;
			bool pressed = (players[i].cmd.buttons & BT_USE) != 0;
			bool fresh = pressed && !held[i];
			held[i] = pressed;
			if (!fresh || box < 0 || face < 0)
				continue;
			Sector s = Level.Sectors[box];
			if (s.floorplane.ZAtPoint(s.centerspot) < boxTop - 1)
				continue;                            // it has sunk (or is sinking): nothing to say
			let mo = players[i].mo;
			FLineTraceData t;
			mo.LineTrace(mo.angle, PlayerPawn(mo) ? PlayerPawn(mo).UseRange : 64, mo.pitch, 0,
				players[i].viewz - mo.pos.z, data: t);
			if (t.HitType != TRACE_HitWall || !t.HitLine || t.HitLine.Index() != face)
				continue;
			if (i == consoleplayer)
				Console.MidPrint(null, "Out of reach for now...");
			Console.Printf("[DMS] CacobeliskShortcutHint: the shortcut box is out of reach from this side");
		}
	}
}

// 2026-11-26 (chat): the yellow station drone, the third kind: a reskinned lost soul. It hovers, stares a moment (its
// visor charging), then flies at the player like a lost soul: the lost soul's stats and attack (A_SkullAttack), the
// drones' look (sprites CBDY, art/drone_sprites.py), sounds and explosion. First shown as a draft in the asset
// browser (the project's assets/), then moved here. Placed as a lost soul with YELLOW_DRONE_TID (CacobeliskDrones).
class CacobeliskYellowDrone : LostSoul
{
	// Note #175 (2026-11-26): a taser: arcs crackle round it as it charges (its sprites, and sparks here), and when it
	// strikes, a jagged arc from it to the player with a zap. LostSoul's own flight ends on a hit with no hook, so the
	// strike is spotted here: flying one tic, stopped the next, with the target within reach.
	const ARC_COLOUR = 0xC8DCFF;    // bluish white (not "ZAP": ZScript ignores case, and Zap() is a method)

	void Crackle()
	{
		for (int i = 0; i < 3; i++)
			A_SpawnParticle(ARC_COLOUR, SPF_FULLBRIGHT, Random(4, 8), FRandom(1.5, 3), 0,
				FRandom(-18, 18), FRandom(-18, 18), FRandom(8, 32), FRandom(-1, 1), FRandom(-1, 1), FRandom(-1, 1));
		if (Random(0, 3) == 0)
			A_StartSound("world/spark", CHAN_BODY, CHANF_NOSTOP, 0.6);
	}

	override void Tick()
	{
		bool flying = bSkullFly;
		Super.Tick();
		if (flying && !bSkullFly && health > 0 && target && Distance3D(target) < radius + target.radius + 24)
			Zap(target);
	}

	void Zap(Actor victim)
	{
		A_StartSound("world/spark", CHAN_WEAPON, 0, 1.0);
		Vector3 a = pos + (0, 0, height / 2);
		Vector3 b = victim.pos + (0, 0, victim.height / 2);
		Vector3 step = (b - a) / 12;
		for (int k = 0; k <= 12; k++)          // a jagged arc between them
		{
			Vector3 p = a + step * k + (FRandom(-4, 4), FRandom(-4, 4), FRandom(-4, 4));
			A_SpawnParticle(ARC_COLOUR, SPF_FULLBRIGHT, Random(6, 10), FRandom(2, 4), 0, p.x - pos.x, p.y - pos.y, p.z - pos.z);
		}
		for (int k = 0; k < 10; k++)           // sparks off the victim
			A_SpawnParticle(ARC_COLOUR, SPF_FULLBRIGHT, Random(8, 14), FRandom(1.5, 3), 0, b.x - pos.x, b.y - pos.y, b.z - pos.z,
				FRandom(-3, 3), FRandom(-3, 3), FRandom(-1, 3), 0, 0, -0.3);
	}

	Default
	{
		+NOBLOOD                 // a machine
		PainChance 96;           // 2026-11-27: the lost soul flinches at every hit; as the red drone now
		SeeSound "baby/sight";
		ActiveSound "cacobelisk/drone/active";   // 2026-11-27: the sputter of static (sndinfo.txt)
		PainSound "cacobelisk/drone/pain";       // the crunch of static (sndinfo.txt), not a groan
		DeathSound "cacobelisk/drone/death";     // the squelch of static, then a small explosion (Death)
		AttackSound "world/spark";   // note #175: its charge: an electric crackle, not the lost soul's scream
		Obituary "%o was zapped by a yellow station drone.";
		DropItem "Cell";         // 2026-11-27 (chat): like the other drones, a small energy cell
		Tag "Yellow station drone";
	}

	States
	{
	Spawn:
		CBDY AB 10 A_Look;
		Loop;
	See:
		CBDY AB 6 A_Chase;
		Loop;
	Missile:
		CBDY C 10 A_FaceTarget;
		CBDY D 4 Bright A_SkullAttack;
	Charge:
		CBDY E 4 Bright Crackle;
		CBDY D 4 Bright Crackle;
		Loop;
	Pain:
		CBDY F 3;
		CBDY F 3 A_StartSound(PainSound, CHAN_VOICE, 0, 1.0, ATTN_NORM, FRandom(0.85, 1.2));   // the static, a little higher or lower each time
		Goto See;
	Death:
		// 2026-11-27 (chat): it hangs there shorting out (the squelch of static, DeathSound), then pops like a
		// lost soul (skull/death, a small explosion).
		CBDY F 10 A_Scream;
	Pop:
		MISL B 8 Bright { A_NoBlocking(); A_StartSound("skull/death", CHAN_BODY); }
		MISL C 6 Bright;
		MISL D 4 Bright;
		Stop;
	}
}

// Note #174 (2026-11-26): the guard posts' zombiemen. They can open their back doors (to come after the player), but
// while they can see the player they stand their ground and shoot through the cage front rather than walking off
// to find a way round: no moving while the player is in sight, and keener to fire than a plain zombieman.
// Placed as zombiemen with GUARD_ZOMBIE_TID, swapped at load (CacobeliskDrones).
class CacobeliskGuardZombie : ZombieMan
{
	Default
	{
		+MISSILEMORE             // fires more readily at range
		MinMissileChance 60;     // (200 is the usual: lower is keener)
	}

	void GuardChase()
	{
		if (target && target.health > 0 && CheckSight(target))
			A_Chase(flags: CHF_DONTMOVE);    // hold the post: turn, and fire when it decides to
		else
			A_Chase();
	}

	States
	{
	See:
		POSS AABBCCDD 4 GuardChase;
		Loop;
	}
}

// 2026-11-27 (chat): the drone gun: "a weapon where you're holding one of the blue drones, and it fires the same
// pattern as they do, and it takes energy cells". The cyan station drone (CacobeliskDrone), held close and seen from
// behind, no hands, a third smaller and hacked open (sprites CBGN, drawn by art/drone_gun.py; the pickup CBGP).
// Rebalanced (2026-11-27, chat: "slightly glitchy - a brief charge, then a sustained sequence of bursts", no longer
// the cyan drone's volleys): a burst of static and a brief charge when the trigger is first pulled, then bursts of
// five bolts, each strayed a little at random (JITTER sideways, JITTER_PITCH up or down: less than the drone's
// 7-degree sweep); held down, burst follows burst (A_ReFire to Hold: no static, no charge).
// Turned down (2026-11-27, chat: "feels too good, better than the minigun"): bolts 5-10 (were 6-12), 4 tics apart
// (were 3), 9 between bursts (were 7), a wider stray (4.5 and 2.25 degrees, were 3 and 1.5). Every bolt landing:
// about 49 a second (it was 79; the chaingun's is about 87, the plasma rifle's about 260). Then (chat): shots 5
// tics apart, 12 between bursts, stray 5.5 and 2.75 degrees, bolts drawn at three quarters size: about 39 a second.
// One cell a bolt, a burst five; it stops short when the cells run out. Slot 6, with the plasma rifle.
// Picked up with a wolf whistle (the drones' whistle repitched: sndinfo.txt, art/wolf_whistle.py).
// A draft in the project's assets/ first; moved here to try in the game (2026-11-27): one on a crate in the station's
// storage room, placed as a plasma rifle with DRONE_GUN_TID and swapped at load (CacobeliskDrones).
class CacobeliskDroneGun : Weapon
{
	const JITTER = 5.5;          // degrees either side a bolt may stray
	const JITTER_PITCH = 2.75;   // ... and up or down
	const SHOT_SEMITONES = 1.0;  // its shot's pitch, above the drone's (then a semitone either way at random)

	Default
	{
		Weapon.SelectionOrder 150;          // after the plasma rifle (100) when the game picks for the player
		Weapon.SlotNumber 6;
		Weapon.SlotPriority 0.5;            // after the plasma rifle on key 6
		Weapon.AmmoType "Cell";
		Weapon.AmmoUse 1;
		Weapon.AmmoGive 40;
		Weapon.BobStyle "Smooth";           // it floats in the hands rather than swinging
		Weapon.BobSpeed 1.4;
		Inventory.PickupMessage "You got a station drone! Somebody's rewired it.";
		Inventory.PickupSound "cacobelisk/dronegun/pickup";   // the wolf whistle
		Tag "Drone gun";
		Radius 14;
		Height 24;
	}

	// One bolt, strayed a little at random: the hacked drone's aim isn't steady.
	action void GlitchShot()
	{
		Actor bolt = A_FireProjectile("CacobeliskGunBolt", FRandom(-JITTER, JITTER), true, 0, 0, 0, FRandom(-JITTER_PITCH, JITTER_PITCH));
		// 2026-11-27 (chat): its shot, the drone's (baby/attack), a semitone higher with a semitone either way at random,
		// played here (the bolt has no SeeSound) so each can have its own pitch; overlapping, so it doesn't cut the static.
		if (bolt)
			A_StartSound("baby/attack", CHAN_WEAPON, CHANF_OVERLAP, 1.0, ATTN_NORM, 2 ** ((SHOT_SEMITONES + FRandom(-1, 1)) / 12.0));
	}

	States
	{
	Spawn:
		CBGP A -1;
		Stop;
	Ready:
		CBGN AAAAAAAAAABBBBBBBBBB 1 A_WeaponReady;
		Loop;
	Select:
		CBGN A 1 A_Raise;
		Loop;
	Deselect:
		CBGN A 1 A_Lower;
		Loop;
	Fire:
		// The static (the drone's sputter, sndinfo.txt) and a brief charge, only as the trigger is first pulled.
		CBGN C 0 A_StartSound("cacobelisk/dronegun/static", CHAN_WEAPON);
		CBGN CD 3;
	Hold:
		// A burst of five, 5 tics apart (the cyan drone's were 6), each bolt with its own sound.
		CBGN E 2 Bright GlitchShot;
		CBGN D 3;
		CBGN E 2 Bright GlitchShot;
		CBGN D 3;
		CBGN E 2 Bright GlitchShot;
		CBGN D 3;
		CBGN E 2 Bright GlitchShot;
		CBGN D 3;
		CBGN E 2 Bright GlitchShot;
		CBGN D 6;
		CBGN C 6 A_ReFire;                  // held down: the next burst, 12 tics on (Hold: no static, no charge)
		Goto Ready;
	}
}

// The drone gun's bolt: the cyan drone's (look, sound, scorch), but a player's weapon: 5 to 10 a bolt (the plasma
// rifle's ball is 5 to 40), so a burst of five that lands is about 37, from five cells.
class CacobeliskGunBolt : CacobeliskDroneBolt
{
	Default
	{
		DamageFunction (Random(5, 10));
		SeeSound "";             // the gun plays the shot itself, each at its own pitch (GlitchShot)
		Scale 0.75;              // (chat) a little smaller than the drone's own
		Radius 3;
		Height 4;
		Obituary "%o was picked off by %k's station drone.";
	}
}
