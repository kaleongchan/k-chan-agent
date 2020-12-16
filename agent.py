'''
This agent employs a basic strategy:
* scan and find the closest target to get to, and repeat
* remember all the bombs and blast area, dodge them at all cost
* won't attempt to bomb any opponent :D
* can be quite dumb to put itself onto a dead end...
'''

import random
import queue
from coderone.dungeon.agent import EntityTags

class Agent:

    ACTIONS = ['','u','d','l','r','p']
    BOMBABLE_TAGS = {
        EntityTags.SoftBlock.value,
        EntityTags.OreBlock.value,
    }

    VISITABLE_TAGS = {
        EntityTags.Treasure.value,
        EntityTags.Ammo.value,
        None,
    }

    DIRECTIONS = {
        (1, 0): 'r',
        (-1, 0): 'l',
        (0, 1): 'u',
        (0, -1): 'd',
    }

    def __init__(self):
        self.bombs_checker = BombsChecker()

    def next_move(self, game_state, player_state):
        self.game_state = game_state
        self.player_state = player_state

        self.bombs_checker.update(game_state)
        self.dangerous_positions = self.bombs_checker.get_dangerous_positions()
        self.bombed_targets = self.bombs_checker.get_bombed_targets()

        target = self.find_target(self.desire_targets())
        return self.get_next_action(target)

    def desire_targets(self):
        targets = {
            EntityTags.Treasure.value,
            EntityTags.Ammo.value,
        }

        if self.player_state.location in self.dangerous_positions:
            targets.add(None)
        elif self.player_state.ammo > 0:
            targets.add(EntityTags.SoftBlock.value)
            targets.add(EntityTags.OreBlock.value)

        return targets

    def find_target(self, targets):
        q = queue.Queue()
        q.put(self.player_state.location)
        self.visited_positions = {self.player_state.location: None}

        while(not q.empty()):
            current = q.get()
            surroundings = [
                (current[0]-1, current[1]),
                (current[0], current[1]-1),
                (current[0]+1, current[1]),
                (current[0], current[1]+1),
            ]
            for pos in surroundings:
                if not self.game_state.is_in_bounds(pos) or pos in self.visited_positions or pos in self.bombed_targets or pos in self.dangerous_positions:
                    continue

                self.visited_positions[pos] = current

                tag = self.game_state.entity_at(pos)

                if tag in targets:
                    q.queue.clear()
                    return {'pos': pos, 'tag': tag}

                if tag in self.VISITABLE_TAGS:
                    q.put(pos)

        return None

    def get_next_action(self, target):
        if not target:
            return ''

        pos = target['pos']
        path = [pos]
        while pos in self.visited_positions:
            prev = self.visited_positions[pos]
            if prev == self.player_state.location:
                break
            path.append(prev)
            pos = prev

        next_to_block = len(path) == 1 and target['tag'] in self.BOMBABLE_TAGS
        if next_to_block:
            return 'p'

        next_pos = path.pop()
        offset = (next_pos[0] - self.player_state.location[0], next_pos[1] - self.player_state.location[1])
        if offset in self.DIRECTIONS:
            return self.DIRECTIONS[offset]

        return ''

class BombsChecker:
    TICKS = 35
    TICKS_AFTER_PLACEMENT = 3
    TICKS_BEFORE_EXPLODE = 2
    RANGE = [1, 2]
    DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    EXPLOSION_BLOCKING_TAGS = {
        EntityTags.IndestructibleBlock.value,
        EntityTags.OreBlock.value,
        EntityTags.SoftBlock.value,
    }

    def __init__(self):
        self.bombs = {}
        self.bombed_targets = {}

    def add_targets(self, bomb):
        # marked the surrounding bombed target
        for d in self.DIRECTIONS:
            for r in self.RANGE:
                pos = (bomb[0] + d[0] * r, bomb[1] + d[1] * r)
                if not self.game_state.is_in_bounds(pos) or self.game_state.entity_at(pos) not in Agent.BOMBABLE_TAGS:
                    continue

                if bomb not in self.bombed_targets:
                    self.bombed_targets[bomb] = []

                self.bombed_targets[bomb].append(pos)

    def remove_targets(self, bomb):
        if bomb in self.bombed_targets:
            del self.bombed_targets[bomb]

    def update(self, game_state):
        self.game_state = game_state
        self.tick = game_state.tick_number
        bombs = set(game_state.bombs)

        # remove old bombs
        old_bombs = set(self.bombs.keys()).difference(bombs)
        for b in old_bombs:
            del self.bombs[b]
            self.remove_targets(b)

        # remember new bombs
        new_bombs = bombs.difference(set(self.bombs.keys()))
        for b in new_bombs:
            self.bombs[b] = self.tick + self.TICKS - 1
            self.add_targets(b)

        self.update_chained_bombs()

    def update_chained_bombs(self):
        # find bombs that explode soon
        tick = self.tick + self.TICKS_BEFORE_EXPLODE
        pending_bombs = {b for b in self.bombs if tick == self.bombs[b]}
        explosions = set()
        for b in pending_bombs:
            for d in self.DIRECTIONS:
                for r in self.RANGE:
                    pos = (b[0] + d[0] * r, b[1] + d[1] * r)
                    if not self.game_state.is_in_bounds(pos) or self.game_state.entity_at(pos) in self.EXPLOSION_BLOCKING_TAGS:
                        break
                    explosions.add(pos)

        for b in self.bombs.keys():
            if b in pending_bombs or b not in explosions:
                continue
            self.bombs[b] = tick + 1

    def get_dangerous_positions(self):
        positions = set(self.bombs.keys())
        dangerous_bombs = [b for b in self.bombs if (self.bombs[b] - self.TICKS + 1) < self.tick and not (self.bombs[b] - self.TICKS + self.TICKS_AFTER_PLACEMENT) < self.tick < (self.bombs[b] - self.TICKS_BEFORE_EXPLODE)]

        for b in dangerous_bombs:
            for d in self.DIRECTIONS:
                for r in self.RANGE:
                    pos = (b[0] + d[0] * r, b[1] + d[1] * r)
                    if not self.game_state.is_in_bounds(pos) or self.game_state.entity_at(pos) in self.EXPLOSION_BLOCKING_TAGS:
                        break
                    positions.add(pos)

        return positions

    def get_bombed_targets(self):
        targets = set()
        for b in self.bombed_targets:
            for t in self.bombed_targets[b]:
                targets.add(t)

        return targets