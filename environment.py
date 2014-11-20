import pygame
import random
from threading import *
import time
import sys
from pybrain.tools.shortcuts import buildNetwork
import math

# Define some colors
BLACK    = (   0,   0,   0)
GREY     = (150, 150 , 150 )
WHITE    = ( 255, 255, 255)
GREEN    = (   0, 255,   0)
RED      = ( 255,   0,   0)
BLUE	 = (   0,   0, 255)
 
pygame.init()
 
# Set the width and height of the screen [width, height]
screensize = (700, 500)
screen = pygame.display.set_mode(screensize)
 
pygame.display.set_caption("evolution")
 
# Loop until the user clicks the close button.
done = False
 
# Used to manage how fast the screen updates
clock = pygame.time.Clock()

# ----------- OBJECTS -----------

habLock = Lock()
habCond = Condition(habLock)

orgSize = 5.0
vegSize = 15.0
initOrgPop = 20
initVegPop = 50
initOrgHealth = 100.0
naturalHealthDec = 0.5
naturalQuantityDec = 0.5
initVegQuantity = 50.0
vegId = 0
orgId = 0
healthFromVeg = 10.0
nature = ["pred", "prey"]
eyeDist = 10
eyeSep = 0.6
viewDist = 50.0
eyeMult = 0.5
eyeSense = 0.0005

generator = None

def addColors(rgb1, rgb2):
	r = rgb1[0] + rgb2[0] if rgb1[0] + rgb2[0] <= 255 else 255
	b = rgb1[1] + rgb2[1] if rgb1[1] + rgb2[1] <= 255 else 255
	g = rgb1[2] + rgb2[2] if rgb1[2] + rgb2[2] <= 255 else 255
	return (r, g, b)

class Habitat(Thread):
	def __init__(self):
		global generator
		Thread.__init__(self)
		self.organisms = pygame.sprite.Group()
		self.vegs = pygame.sprite.Group()
		generator = OrganismGenerator(self)
		generator.start()
		VeggieGenerator(self).start()

	def getUnoccupiedSpace(self): # inefficient
		while True:
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			tmp = tmpSprite(orgSize, orgSize)
			tmp.rect.x = x
			tmp.rect.y = y
			with habLock:
				collisions = pygame.sprite.spritecollide(tmp, self.organisms, False)
				if collisions == []:
					return (x, y)
				else:
					continue

	def run(self):
		while True:
			time.sleep(1)
			if self.organisms == []:
				print("mass extinction")
				break
			pass

class tmpSprite(pygame.sprite.Sprite):
	def __init__(self, width, height):
		super().__init__() # sprite constructor
		self.rect = pygame.Surface([width, height]).get_rect()

class VeggieGenerator(Thread):
	def __init__(self, habitat):
		Thread.__init__(self)
		self.habitat = habitat
		self.initializeVegPop()

	def initializeVegPop(self):
		global vegId
		for i in range(initVegPop):
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			veg = Veg(vegId, x, y, initVegQuantity, self.habitat)
			veg.start()
			with habLock:
				self.habitat.vegs.add(veg)
				vegId += 1

	def run(self):
		global vegId
		while True:
			time.sleep(1)
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			veg = Veg(vegId, x, y, initVegQuantity, self.habitat)
			veg.start()
			with habLock:
				self.habitat.vegs.add(veg)
				vegId += 1

class Veg(pygame.sprite.Sprite, Thread):
	def __init__(self, id, initX, initY, maxQuantity, habitat):
		Thread.__init__(self)
		self.color = GREEN
		self.id = id
		self.habitat = habitat
		self.maxQuantity = maxQuantity
		self.quantity = maxQuantity
		self.eaten = 0

		super().__init__() # sprite constructor
		self.rect = pygame.Surface([vegSize, vegSize]).get_rect()
		self.rect.x = initX
		self.rect.y = initY

	def getQuantityColor(self):
		quantityFraction = self.quantity / self.maxQuantity
		levels = 1 - quantityFraction
		return (int(round(255 * levels)), 255, int(round(255 * levels)))

	def update(self):
		self.quantity -= naturalQuantityDec + self.eaten
		self.eaten = 0
		self.color = self.getQuantityColor()
		if self.quantity <= 0:
			return False # dead
		return True

	def run(self):
		while True:
			time.sleep(0.5)
			with habLock:
				if not self.update(): # death
					try:
						self.habitat.vegs.remove(self)
						break
					except:
						print("attempted to remove non-existant veg")

class OrganismGenerator(Thread):
	def __init__(self, habitat):
		Thread.__init__(self)
		self.habitat = habitat
		self.initializeOrgPop()
		self.babyQueue = []
		self.babyQueueMutex = Lock()
		

	def initializeOrgPop(self):
		global orgId
		for i in range(initOrgPop):
			(x, y) = self.habitat.getUnoccupiedSpace()
			nat = random.choice(nature)
			organism = Organism(orgId, 0, x, y, initOrgHealth, nat, self.habitat)
			organism.start()
			with habLock:
				self.habitat.organisms.add(organism)
				orgId += 1

	#creates the actual organism given two parents, of the supposed same nature
	def createBaby(self, parent1, parent2):
		parent1Genes = parent1.brain.params
		parent2Genes = parent2.brain.params
		crossover = random.randint(0,len(parent1Genes) - 1)
		newGenes = []
		for i in range(crossover):
			newGenes.append(parent1Genes[i])
		for j in range(crossover, len(parent1Genes)):
			newGenes.append(parent2Genes[j])
		global orgId
		baby = Organism(orgId, parent1.generation + 1, parent1.rect.x, parent1.rect.y, initOrgHealth, parent1.nature, self.habitat)
		return baby

	def addToBeBornBaby(self, parent1, parent2):
		with self.babyQueueMutex:
			print ("HAVING SEX")
			newBaby = self.createBaby(parent1, parent2)
			self.babyQueue.append(newBaby)

	def run(self):
		global orgId
		while True:
			time.sleep(5)
			newBaby = None
			with self.babyQueueMutex:
				if len(self.babyQueue) != 0:
					newBaby = self.babyQueue.pop(0)
			if not(newBaby is None):
				with habLock:
					self.habitat.organisms.add(newBaby)
					newBaby.start()
					orgId += 1
			#(x, y) = self.habitat.getUnoccupiedSpace()
			#nat = random.choice(nature)
			#organism = Organism(orgId, 0, x, y, initOrgHealth, nat, self.habitat)
			#organism.start()
			#with habLock:
				#self.habitat.organisms.add(organism)
				#orgId += 1

class Organism(pygame.sprite.Sprite, Thread):
	def __init__(self, id, generation, initX, initY, maxHealth, nature, habitat):
		Thread.__init__(self)
		super().__init__()
		self.color = BLACK
		self.generation = generation
		self.id = id
		self.speed = 2
		self.iterationsUntilMate = 0
		self.velX = 0
		self.velY = 0
		self.habitat = habitat
		self.maxHealth = maxHealth
		self.health = maxHealth
		self.damageTaken = 0
		self.nature = nature
		self.indicatorColor = RED if self.nature == "pred" else BLUE
		self.orientation = random.uniform(0, 2 * math.pi) # polar
		self.rect = pygame.Surface([orgSize, orgSize]).get_rect()
		self.rect.x = initX
		self.rect.y = initY
		self.age = 0
		self.eyes = None
		self.brain = buildNetwork(6,4,2)
		self.leftVision = (0, 0, 0)
		self.rightVision = (0, 0, 0)
		self.orient()
		
		self.closestVeg = None
		self.look()
		# self.brain = Brain()

	def getHealthColor(self):
		healthFraction = self.health / self.maxHealth
		levels = 1 - healthFraction
		return (int(round(255 * levels)), int(round(255 * levels)), int(round(255 * levels)))

	def orient(self):
		# random for now
		if self.age % 5 == 0: # for now, make changing directions based on age
			inputs = []
			for color in self.leftVision:
				inputs.append(color)
			for color in self.rightVision:
				inputs.append(color)

			outputs = self.brain.activate(inputs)
			if outputs[0] > outputs[1]:
				self.orientation -= 0.1
			else:
				self.orientation += 0.1
			#self.orientation = random.uniform(0, 2 * math.pi)
			self.speed = random.randrange(5)
		# body stays stationary and moves in orientation and velocity
		# calculate position of eyes (two points)
		(centx, centy) = self.rect.center
		leyeX = int(round(centx + eyeDist * math.cos(self.orientation - eyeSep)))
		leyeY = int(round(centy + eyeDist * math.sin(self.orientation - eyeSep)))
		reyeX = int(round(centx + eyeDist * math.cos(self.orientation + eyeSep)))
		reyeY = int(round(centy + eyeDist * math.sin(self.orientation + eyeSep)))
		self.eyes = ((leyeX, leyeY), (reyeX, reyeY))

		self.velX = self.speed * math.cos(self.orientation)
		self.velY = self.speed * math.sin(self.orientation)

	def move(self):

		# update position
		self.rect.x += self.velX
		self.rect.y += self.velY

		self.orient()

		# check collisions
		if self.rect.y > screensize[1]:
			self.rect.y = 0
			self.orient()
		elif self.rect.y < 0:
			self.rect.y = screensize[1]
			self.orient()
		if self.rect.x > screensize[0]:
			self.rect.x = 0
			self.orient()
		elif self.rect.x < 0:
			self.rect.x = screensize[0]
			self.orient()

	def look(self):
		minDist = 99999.0
		for veg in self.habitat.vegs:
			distToVeg = math.sqrt(math.pow(self.rect.center[0] - veg.rect.center[0], 2) + math.pow(self.rect.center[1] - veg.rect.center[1], 2))
			# update inputs to brain
			if distToVeg < viewDist:
				self.leftVision = addColors(self.leftVision, veg.color)

			# update closest veggie
			if distToVeg < minDist:
				minDist = distToVeg
				self.closestVeg = veg

		# for org in self.habitat.orgs:
		# 	distToVeg = math.sqrt(math.pow(self.rect.center[0] - veg.rect.center[0], 2) + math.pow(self.rect.center[1] - veg.rect.center[1], 2))
		# 	# update inputs to brain
		# 	if distToVeg < viewDist:
		# 		self.leftVision = addColors(self.leftVision, veg.color)

	def update(self):

		global generator
		# update health
		self.health -= naturalHealthDec + self.damageTaken
		self.damageTaken = 0
		self.color = self.getHealthColor()
		if self.health <= 0:
			return False # dead

		self.age += 1

		# check eyes
		self.look()
		# set orientation involves output from brain
		self.move()

		# check for collision(s) with others. inefficient?
		for org in self.habitat.organisms:
			if org == self:
				continue

			if pygame.sprite.collide_rect(self, org):
				# collision.
				#if collided parents can mate
				if (self.iterationsUntilMate == 0) and (org.iterationsUntilMate == 0):
					if random.randint(0,1) == 0:
						generator.addToBeBornBaby(self, org)
						self.iterationsUntilMate = 10
						org.iterationsUntilMate = 10
				self.rect.x += -1 * self.velX
				self.rect.y += -1 * self.velY

		# check for "collision" with food. mmm...
		for veg in self.habitat.vegs:
			if pygame.sprite.collide_rect(self, veg):
				veg.eaten += 1
				self.health += healthFromVeg # how to prevent gorging?
				if self.health > self.maxHealth:
					self.health = self.maxHealth

		return True

	def run(self):
		while True:
			time.sleep(.2) # rest
			with habLock:
				if not self.update(): # death
					try:
						self.habitat.organisms.remove(self)
						break
					except:
						print("attempted to remove non-existant organism")

habitat = Habitat()
habitat.start()

# ----------- OBJECTS -------

# -------- Main Program Loop -----------
while not done:
	# --- Main event loop
	for event in pygame.event.get(): # User did something
		if event.type == pygame.QUIT: # If user clicked close
			done = True # Flag that we are done so we exit this loop
 
	# --- Game logic should go here
 
	# --- Drawing code should go here
 
	# First, clear the screen to white. Don't put other drawing commands
	# above this, or they will be erased with this command.
	screen.fill(WHITE)

	# draw food
	with habLock:
		for veg in habitat.vegs:
			pygame.draw.rect(screen, veg.color, [veg.rect.x, veg.rect.y, veg.rect.width, veg.rect.height])
		for org in habitat.organisms:
			pygame.draw.rect(screen, org.color, [org.rect.x, org.rect.y, org.rect.width, org.rect.height])
			pygame.draw.rect(screen, org.indicatorColor, [org.rect.x + org.rect.width, org.rect.y, 2, 2])
			pygame.draw.circle(screen, BLACK, (org.eyes[0][0], org.eyes[0][1]), 2, 1)
			pygame.draw.lines(screen, BLACK, False, [org.rect.center, (org.eyes[0][0], org.eyes[0][1])], 1)
			pygame.draw.circle(screen, BLACK, (org.eyes[1][0], org.eyes[1][1]), 2, 1)
			pygame.draw.lines(screen, BLACK, False, [org.rect.center, (org.eyes[1][0], org.eyes[1][1])], 1)
			if org.closestVeg:
				pygame.draw.lines(screen, GREY, False, [org.rect.center, org.closestVeg.rect.center])

	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 10 frames per second
	clock.tick(5)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()