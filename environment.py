import pygame
import random
from threading import *
import time
import sys
import matplotlib.pyplot as plt
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
screensize = (1000, 1000)
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
initOrgPop = 50
initVegPop = 40
initOrgHealth = 100.0
naturalHealthDec = 0.5
naturalQuantityDec = 0.5
initVegQuantity = 50.0
vegId = 0
orgId = 0
preyHealthFromVeg = 10.0
predHealthFromVeg = 2.0
healthFromPrey = 100.0
nature = ["pred", "prey"]
eyeDist = 15
eyeSep = 1
viewDist = 50.0
eyeMult = 1.5
eyeSense = 0.0005

mutationPr = 0.03
mutationSvr = 0.5

generator = None
oldestAge = 0

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
			time.sleep(0.25)
			randomFactor = random.uniform(0,1)
			#randomly
			if randomFactor > 0.6:
				x = random.randrange(screensize[0])
				y = random.randrange(screensize[1])
			#make veggies in one of  two clusters
			else:
				secondRandomFactor = random.uniform(0,1)
				#right cluster
				if secondRandomFactor < 0.5:
					x = random.randrange((screensize[0] * 6)/10, (screensize[0] * 8)/10)
				#left cluster
				else:
					x = random.randrange((screensize[0] * 2)/10, (screensize[0] * 4)/10)
				y = random.randrange((screensize[1] * 3)/10, (screensize[1] * 7)/10)
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
			time.sleep(0.25)
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
		global orgId
		parent1Genes = parent1.brain.params
		parent2Genes = parent2.brain.params

		crossover = random.randrange(len(parent1Genes))
		newGenes = parent1Genes.tolist()[:crossover] + parent2Genes.tolist()[crossover:]
		if (random.random() < mutationPr):
			geneToMutateIndex = random.randint(0, (len(newGenes) - 1))
			newGenes[geneToMutateIndex] += mutationSvr
		generation = parent1.generation + 1 if parent1.generation > parent2.generation else parent2.generation + 1
		baby = Organism(orgId, generation, parent1.rect.x, parent1.rect.y, parent1.maxHealth, parent1.nature, self.habitat)
		baby.brain._setParameters(newGenes)
		orgId += 1
		return baby

	def addToBeBornBaby(self, parent1, parent2):
		newBaby = self.createBaby(parent1, parent2)
		self.babyQueue.append(newBaby)

	def run(self):
		global orgId
		while True:
			time.sleep(2)
			with habLock:
				if self.babyQueue != []:
					newBaby = self.babyQueue.pop(0)
					self.habitat.organisms.add(newBaby)
					newBaby.start()

			if random.uniform(0,1) <= mutationPr:
				# mutations introduced to population gene pool via new organisms with random brains
				(x, y) = self.habitat.getUnoccupiedSpace()
				nat = random.choice(nature)
				organism = Organism(orgId, 0, x, y, initOrgHealth, nat, self.habitat)
				organism.start()
				with habLock:
					self.habitat.organisms.add(organism)
					orgId += 1
					print("mutation! %d" % orgId)

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
		self.brain = buildNetwork(8,4,2)
		self.leftVision = (0, 0, 0)
		self.rightVision = (0, 0, 0)
		self.friendsNear = 0
		self.orient()
		self.age = 0
		
		self.closestVeg = None
		self.look()
		# self.brain = Brain()

	def getHealthColor(self):
		healthFraction = self.health / self.maxHealth
		levels = 1 - healthFraction
		return (int(round(255 * levels)), int(round(255 * levels)), int(round(255 * levels)))

	def incrementAge(self):
		global oldestAge
		self.age += 1
		if self.age > oldestAge:
			oldestAge = self.age

	def orient(self):
		# random for now
		# if self.age % 2 == 0: # for now, make changing directions based on age,
		inputs = []
		for color in self.leftVision:
			inputs.append(color)
		for color in self.rightVision:
			inputs.append(color)
		inputs.extend([1,1]) # bias neurons
		# print(inputs)

		outputs = self.brain.activate(inputs)
		lrDiff = outputs[0] - outputs[1]

		if math.fabs(lrDiff) < 0.1:
			pass
		elif lrDiff < 0:
			self.orientation -= 0.05
		else:
			self.orientation += 0.05

		#self.orientation = random.uniform(0, 2 * math.pi)
		self.speed = random.uniform(0,3)

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

		# wrap around screen
		if self.rect.y >= screensize[1]:
			self.rect.y = 1
		
		if self.rect.y <= 0:
			self.rect.y = screensize[1] - 1

		if self.rect.x >= screensize[0]:
			self.rect.x = 1
		
		if self.rect.x <= 0:
			self.rect.x = screensize[0] - 1

		self.orient()

	def look(self):
		minDist = 9999.0
		lv = [0,0,0]
		rv = [0,0,0]
		self.friendsNear = 0
		for veg in self.habitat.vegs:
			distToVeg = math.sqrt(math.pow(self.rect.center[0] - veg.rect.center[0], 2) + math.pow(self.rect.center[1] - veg.rect.center[1], 2))
			if distToVeg < viewDist:
				smell = eyeMult * math.exp(-eyeSense * (math.pow(self.eyes[0][0] - veg.rect.center[0],2) + math.pow(self.eyes[0][1] - veg.rect.center[1],2)))
				lv = [lv[0] + smell * veg.color[0], lv[1] + smell * veg.color[1], lv[2] + smell * veg.color[2]]
				smell = eyeMult * math.exp(-eyeSense * (math.pow(self.eyes[1][0] - veg.rect.center[0],2) + math.pow(self.eyes[1][1] - veg.rect.center[1],2)))
				rv = [rv[0] + smell * veg.color[0], rv[1] + smell * veg.color[1], rv[2] + smell * veg.color[2]]

			# update closest veggie
			if distToVeg < minDist:
				minDist = distToVeg
				self.closestVeg = veg

		for org in self.habitat.organisms:
			if org == self:
				continue
			distToOrg = math.sqrt(math.pow(self.rect.center[0] - org.rect.center[0], 2) + math.pow(self.rect.center[1] - org.rect.center[1], 2))
			# update inputs to brain
			if distToOrg < viewDist:
				if org.nature == self.nature:
					self.friendsNear += 1
				smell = eyeMult * math.exp(-eyeSense * (math.pow(self.eyes[0][0] - org.rect.center[0],2) + math.pow(self.eyes[0][1] - org.rect.center[1],2)))
				lv = [lv[0] + smell * org.indicatorColor[0], lv[1] + smell * org.indicatorColor[1], lv[2] + smell * org.indicatorColor[2]]
				smell = eyeMult * math.exp(-eyeSense * (math.pow(self.eyes[1][0] - org.rect.center[0],2) + math.pow(self.eyes[1][1] - org.rect.center[1],2)))
				rv = [rv[0] + smell * org.indicatorColor[0], rv[1] + smell * org.indicatorColor[1], rv[2] + smell * org.indicatorColor[2]]

		self.leftVision = tuple([signal for signal in lv])
		self.rightVision = tuple([signal for signal in rv])

	def canEat(self, org):
		natureOK = org.nature == "prey" and self.nature == "pred"
		return natureOK

	def healthGained(self, org):
		return org.health * (self.friendsNear if not self.friendsNear == 0 else 1) / (org.friendsNear if not org.friendsNear == 0 else 2)

	def canMate(self):
		# print("can mate?" + str(self.health/self.maxHealth))
		healthOK = (self.health / self.maxHealth) > 0.4
		return healthOK

	def shouldMate(self, org):
		# print("shouldMate?" + str(org.health/org.maxHealth))
		healthOK = (org.health / org.maxHealth) > 0.6
		ageOK = org.age < self.age
		# ageOK = True
		return healthOK and ageOK

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
				# collision. move away for now.
				if self.canEat(org):
					healthTrans = self.healthGained(org)
					org.damageTaken += healthTrans
					self.health += healthTrans
					if self.health > self.maxHealth:
						self.health = self.maxHealth
				if self.canMate() and self.shouldMate(org):
					print("mating" + str(self.id) + " " + str(org.id))
					generator.addToBeBornBaby(self, org)
				# self.rect.x += -6 * self.velX
				# self.rect.y += -6 * self.velY
				break

		# check for "collision" with food. mmm...
		for veg in self.habitat.vegs:
			if pygame.sprite.collide_rect(self, veg):
				veg.eaten += 1
				self.health += preyHealthFromVeg if self.nature == "prey" else predHealthFromVeg# how to prevent gorging?
				if self.health > self.maxHealth:
					self.health = self.maxHealth
		return True

	def run(self):
		while True:
			time.sleep(.1) # rest
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
iteration = 0
iteration_x_values = []
maxAge_y_values = []

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



	#counter for xvalues
	

	# draw food
	with habLock:
		# print(iteration)
		iteration_x_values.append(iteration)
		for veg in habitat.vegs:
			pygame.draw.rect(screen, veg.color, [veg.rect.x, veg.rect.y, veg.rect.width, veg.rect.height])

		maxAge = 0
		for org in habitat.organisms:
			org.incrementAge()
			if org.age > maxAge:
				maxAge = org.age
			pygame.draw.rect(screen, org.color, [org.rect.x, org.rect.y, org.rect.width, org.rect.height])
			pygame.draw.rect(screen, org.indicatorColor, [org.rect.x + org.rect.width, org.rect.y, 2, 2])
			pygame.draw.circle(screen, BLACK, (org.eyes[0][0], org.eyes[0][1]), 2, 1)
			pygame.draw.lines(screen, BLACK, False, [org.rect.center, (org.eyes[0][0], org.eyes[0][1])], 1)
			pygame.draw.circle(screen, BLACK, (org.eyes[1][0], org.eyes[1][1]), 2, 1)
			pygame.draw.lines(screen, BLACK, False, [org.rect.center, (org.eyes[1][0], org.eyes[1][1])], 1)
			# if org.closestVeg:
			# 	pygame.draw.lines(screen, GREY, False, [org.rect.center, org.closestVeg.rect.center])
		maxAge_y_values.append(maxAge)
		iteration += 1
			# if org.id == 1:
			# 	pygame.draw.rect(screen, GREEN, [org.rect.x + org.rect.width, org.rect.y + org.rect.height, 2, 2])
			# 	pygame.draw.rect(screen, org.leftVision, [0, 0, 20, 20])
			# 	pygame.draw.rect(screen, org.rightVision, [30, 0, 20, 20])

	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 10 frames per second
	clock.tick(20)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()