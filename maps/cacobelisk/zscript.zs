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

	void LockSwitches(Line used)
	{
		TextureID off = TexMan.CheckForTexture("SW1GRAY", TexMan.Type_Wall);
		TextureID on = TexMan.CheckForTexture("SW2GRAY", TexMan.Type_Wall);
		shutAt = Level.maptime + SHUT_DELAY;
		for (int i = 0; i < Level.Lines.Size(); i++)
		{
			Line l = Level.Lines[i];
			if (l.args[0] == CAR_TAG && l.special == Floor_LowerByValue)
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
		if (!broken)
		{
			if (car.floorplane.ZAtPoint(car.centerspot) > LANDED_Z + 0.5)
				return;
			broken = true;
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

	const SHOTGUN_TID = 300;
	const SHOW_DELAY = 105;      // tics from the landing to the first obelisk (3 s)
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
		if (!switchShown && switchSleeve >= 0 && (shotgun == null || shotgun.Owner != null))
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
		if (isSwitch)
		{
			// Note #38: the slit the violet spills from (cut into the sleeve's back, map.py slit_edges)
			// opens upwards as the sleeve sinks, its top rising to the sleeve's at the same speed, so
			// nothing of it is left standing once the slab is uncovered.
			let slits = Level.CreateSectorTagIterator(SLIT_TAG);
			int k;
			while ((k = slits.Next()) >= 0)
			{
				Sector slit = Level.Sectors[k];
				double rise = sec.ceilingplane.ZAtPoint(sc) - slit.ceilingplane.ZAtPoint(slit.centerspot);
				Level.CreateCeiling(slit, Ceiling.ceilRaiseByValue, null, SINK_SWITCH, SINK_SWITCH, rise);
			}
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
			QueueSplats(pair);
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
				mo.A_StartSound("*usefail", CHAN_VOICE);
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
