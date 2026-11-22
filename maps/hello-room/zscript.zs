version "4.10"

// Hello room's own script (dms packs it into this map's WAD; it runs on this map only).
// In-game notes #15-#19: when the player enters the hallway, the yard lifts bring the lost souls up
// (line hall.mouth_n, Floor_RaiseByValue on tag YARD_TAG, set in map.py), and this wakes them at the
// same moment, already after the player, seen or not (a NoiseAlert line didn't reach them).

class HelloRoomYards : EventHandler
{
	const YARD_TAG = 1;     // the yards' sector tag (map.py YARD_TAG)
	const SOULS_TID = 10;   // the lost souls' thing id (map.py SOULS_TID)

	override void WorldLineActivated(WorldEvent e)
	{
		Line ln = e.ActivatedLine;
		if (ln == null || ln.special != Floor_RaiseByValue || ln.args[0] != YARD_TAG || e.Thing == null)
			return;
		int woken = 0;
		let it = Level.CreateActorIterator(SOULS_TID);
		Actor soul;
		while ((soul = it.Next()) != null)
		{
			if (soul.health <= 0 || soul.target == e.Thing)
				continue;
			soul.target = e.Thing;
			soul.SetState(soul.SeeState);
			woken++;
		}
		Console.Printf("[DMS] HelloRoomYards: the yards rise; woke %d lost soul(s)", woken);
	}
}
