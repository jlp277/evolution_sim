import pygame
import random
from threading import *
import time
import sys

# Define some colors
BLACK    = (   0,   0,   0)
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

orgSize = 5
vegSize = 15
initOrgPop = 20
initVegPop = 50
initOrgHealth = 100.0
naturalHealthDec = 0.5
naturalQuantityDec = 0.5
initVegQuantity = 50.0
vegId = 0
orgId = 0
healthFromVeg = 10
nature = ["pred", "prey"]

viewDistanceX = screensize[0]/8
viewDistanceY = screensize[1]/8

class Habitat(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.organisms = []
		self.vegs = []
		OrganismGenerator(self).start()
		VeggieGenerator(self).start()

	def getUnoccupiedSpace(self): # inefficient
		while True:
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			tmp = tmpSprite(orgSize, orgSize)
			tmp.rect.x = x
			tmp.rect.y = y
			siamese = False
			with habLock:
				for org in self.organisms:
					if pygame.sprite.collide_rect(tmp, org):
						siamese = True
				if siamese == False:
					return (x, y)

	def run(self):
		while True:
			time.sleep(1)
			if self.organisms == []:
				print("mass extinction")
				# would be nice to kill all threads here. only vegs would need to be killed.
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
				self.habitat.vegs.append(veg)
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
				self.habitat.vegs.append(veg)
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

	def initializeOrgPop(self):
		global orgId
		for i in range(initOrgPop):
			(x, y) = self.habitat.getUnoccupiedSpace()
			nat = random.choice(nature)
			organism = Organism(orgId, 0, x, y, initOrgHealth, nat, self.habitat)
			organism.start()
			with habLock:
				self.habitat.organisms.append(organism)
				orgId += 1

	def run(self):
		global orgId
		while True:
			time.sleep(5)
			(x, y) = self.habitat.getUnoccupiedSpace()
			nat = random.choice(nature)
			organism = Organism(orgId, 0, x, y, initOrgHealth, nat, self.habitat)
			organism.start()
			with habLock:
				self.habitat.organisms.append(organism)
				orgId += 1

class Eye(pygame.sprite.Sprite):
	def __init_(self, width, height):
		super().__init__()
		self.image = pygame.Surface([width, height])
		self.rect = self.image.get_rect()

class Organism(pygame.sprite.Sprite, Thread):
	def __init__(self, id, generation, initX, initY, maxHealth, nature, habitat):
		Thread.__init__(self)
		super().__init__()
		self.color = BLACK
		self.generation = generation
		self.id = id
		self.orientation = 0 # polar
		self.velX = 1
		self.velY = 1
		self.habitat = habitat
		self.maxHealth = maxHealth
		self.health = maxHealth
		self.damageTaken = 0
		self.nature = nature
		self.indicatorColor = RED if self.nature == "pred" else BLUE
		self.age = 0
		# self.leftEye = Eye(viewDistanceX, viewDistanceY)
		# self.rightEye = Eye(viewDistanceX, viewDistanceY)
		# self.brain = Brain()

		self.rect = pygame.Surface([orgSize, orgSize]).get_rect()
		self.rect.x = initX
		self.rect.y = initY

	def getHealthColor(self):
		healthFraction = self.health / self.maxHealth
		levels = 1 - healthFraction
		return (int(round(255 * levels)), int(round(255 * levels)), int(round(255 * levels)))

	def update(self):

		# update health
		self.health -= naturalHealthDec + self.damageTaken
		self.damageTaken = 0
		self.color = self.getHealthColor()
		if self.health <= 0:
			return False # dead

		self.age += 1

		""" ** UPDATE SPRITE AFTER WHENEVER POS IS UPDATED ** """
		# update position
		self.rect.x += self.velX
		self.rect.y += self.velY

		# check collisions
		if self.rect.y > screensize[1]:
			self.rect.y = screensize[1]
		elif self.rect.y < 0:
			self.rect.y = 0
		if self.rect.x > screensize[0]:
			self.rect.x = screensize[0]
		elif self.rect.x < 0:
			self.rect.x = 0

		# check for collision(s) with others. inefficient?
		for org in self.habitat.organisms:
			if org == self:
				continue
			if pygame.sprite.collide_rect(self, org):
				# collision. move away for now.
				self.rect.x += -1 * self.velX
				self.rect.y += -1 * self.velY

		# random directions
		if self.age % 5 == 0: # for now, make changing directions based on age
			self.velX = random.choice([-1,1]) * random.randrange(10)
			self.velY = random.choice([-1,1]) * random.randrange(10)

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

	# draw animals
	with habLock:
		for org in habitat.organisms:
			pygame.draw.rect(screen, org.color, [org.rect.x, org.rect.y, org.rect.width, org.rect.height])
			pygame.draw.rect(screen, org.indicatorColor, [org.rect.x + org.rect.width, org.rect.y, 2, 2])

	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 10 frames per second
	clock.tick(10)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()