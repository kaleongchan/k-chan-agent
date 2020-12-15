# import external packages
import random
import queue
from coderone.dungeon.agent import EntityTags

class Agent:

    ACTIONS = ['','u','d','l','r','p']
    VISITABLE_TAGS = {
        EntityTags.Treasure.value,
        EntityTags.Ammo.value,
        None
    }

    DIRECTIONS = {
        (1, 0): 'r',
        (-1, 0): 'l',
        (0, 1): 'u',
        (0, -1): 'd',
    }
    
    def __init__(self):
        '''
        Place any initialisation code for your agent here (if any)

        '''

        self.bombs = BombsChecker()
        self.ignore_targets = set()
        
    def next_move(self, game_state, player_state):
        '''
        This method is called each time your Agent is required to choose an action
        
        '''
        action = ''

        # grab up to date data
        self.update(game_state, player_state)
        
        # determine target type
        if len(game_state.treasure) > 0:
            target = EntityTags.Treasure.value
        elif player_state.ammo == 0:
            target = EntityTags.Ammo.value
        elif len(game_state.soft_blocks) > 0:
            target = EntityTags.SoftBlock.value
        else:
            target = EntityTags.OreBlock.value


        # find shortest / safest path
        self.queue = queue.Queue()
        self.queue.put(player_state.location)
        self.visited_cells = {player_state.location: None}
        target_pos = None
        while(not self.queue.empty()): 
            current = self.queue.get()
            surroundings = [
                (current[0]-1, current[1]),
                (current[0], current[1]-1),
                (current[0]+1, current[1]),
                (current[0], current[1]+1),
            ]
            for pos in surroundings:
                if not self.game_state.is_in_bounds(pos):
                    continue

                if pos in self.visited_cells:
                    continue

                tag = self.game_state.entity_at(pos)

                # if tag in self.VISITABLE_TAGS:
                self.visited_cells[pos] = current        

                if tag == target and pos not in self.ignore_targets:
                    print('found target', target, pos)
                    self.queue.queue.clear()
                    target_pos = pos
                    break
                
                if tag in self.VISITABLE_TAGS:
                    self.queue.put(pos)
        
        if target_pos != None:
            pos = target_pos
            path = [pos]
            while pos in self.visited_cells:
                prev = self.visited_cells[pos]
                if prev == player_state.location:
                    break
                path.append(prev)
                pos = prev

            if len(path) == 1 and target not in self.VISITABLE_TAGS:
                action = 'p'
                self.ignore_targets.add(target_pos)
            else:
                next_pos = path.pop()
                offset = (next_pos[0] - player_state.location[0], next_pos[1] - player_state.location[1])
                if offset in self.DIRECTIONS:
                    action = self.DIRECTIONS[offset]
        else:
            # find a safe place
            print('find a safe place')

        print(game_state.tick_number, target, action)

        return action


    def update(self, game_state, player_state):
        self.columns = game_state.size[0]
        self.rows = game_state.size[1]
        self.game_state = game_state
        self.bombs.update(game_state.bombs, game_state.tick_number)
        
        
            
class BombsChecker:
    BOMB_TICKS = 35

    def __init__(self):
        self.bombs = {}
        
    def update(self, bombs, tick):

        # remove old bombs
        old_bombs = set(self.bombs.keys()).difference(set(bombs))
        for b in old_bombs:
            del self.bombs[b]
            print("T{} bomb explode".format(tick), b)

        # remember new bombs
        new_bombs = set(bombs).difference(set(self.bombs.keys()))
        for b in new_bombs:
            self.bombs[b] = tick + self.BOMB_TICKS - 1
            print("new bomb at {}, will explode at tick {}".format(b, self.bombs[b]))

        # sortedBombs = [item[0] for item in sorted(self.bombs.items(), key=lambda item: item[1])]
        # for i in range(1, len(sortedBombs)):
        #     inRange = self.inBlastRange(sortedBombs[i-1], sortedBombs[i])
        #     print('chained', inRange)

        

    def get_blast_locations(self, tick):
        pending_bombs = [b for b in self.bombs if self.bombs[b] == tick]
        locations = set()

        for b in pending_bombs:
            locations = locations.union({
                (b[0], b[1] - 2), 
                (b[0], b[1] - 1), 
                b, 
                (b[0], b[1] + 1), 
                (b[0], b[1] + 2), 
                (b[0] - 2, b[1]), 
                (b[0] - 1, b[1]), 
                (b[0] + 1, b[1]), 
                (b[0] + 2, b[1]),     
            })

        return locations
