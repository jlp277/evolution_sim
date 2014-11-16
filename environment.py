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
vegSize = 10
initPopSize = 20
initOrgHealth = 10
naturalHealthDec = 0.1
naturalQuantityDec = 1
initVegQuantity = 10
vegId = 0
healthFromVeg = 1

class Habitat(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.organisms = []
		self.vegs = []
		VeggieGenerator(self).start()
		for id in range(initPopSize):
			with habLock:
				(x, y) = self.getUnoccupiedSpace()
				organism = Organism(id, 0, x, y, initOrgHealth, self)
				organism.start()
				self.organisms.append(organism)

	def getUnoccupiedSpace(self): # inefficient
		while True:
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			tmpBody = OrganismBody(orgSize, orgSize)
			tmpBody.rect.x = x
			tmpBody.rect.y = y
			siamese = False
			for org in self.organisms:
				if pygame.sprite.collide_rect(tmpBody, org.body):
					siamese = True
			if siamese == False:
				return (x, y)

	def run(self):
		while True:
			if self.organisms == []:
				print("mass extinction")
				break
			pass

class VeggieGenerator(Thread):
	def __init__(self, habitat):
		Thread.__init__(self)
		self.habitat = habitat

	def run(self):
		global vegId
		while True:
			time.sleep(5)
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			veg = Veg(vegId, x, y, initVegQuantity, self.habitat)
			veg.start()
			with habLock:
				self.habitat.vegs.append(veg)
				vegId += 1

class VegBody(pygame.sprite.Sprite):
	def __init__(self, width, height):
		super().__init__() # sprite constructor
		self.image = pygame.Surface([width, height])
		self.rect = self.image.get_rect()

class Veg(Thread):
	def __init__(self, id, initX, initY, quantity, habitat):
		Thread.__init__(self)
		self.color = GREEN
		self.sizeX = vegSize
		self.sizeY = vegSize
		self.id = id
		self.posX = initX
		self.posY = initY
		self.habitat = habitat
		self.body = VegBody(self.sizeX, self.sizeY)
		self.quantity = quantity
		self.eaten = 0

	def update(self):
		self.quantity -= naturalQuantityDec + self.eaten
		self.eaten = 0
		self.color = (255 - (255 * ((self.quantity + 0.0)/initVegQuantity)), 255, 255 - (255 * ((self.quantity + 0.0)/initVegQuantity)))
		if self.quantity <= 0:
			return False # dead
		return True

	def run(self):
		while True:
			time.sleep(2)
			with habLock:
				if not self.update(): # death
					try:
						self.habitat.vegs.remove(self)
						print("foods list with %d removed:" % self.id)
						for veg in self.habitat.vegs:
							print("%d, " % veg.id)
						break
					except:
						print("attempted to remove non-existant veg")

class OrganismBody(pygame.sprite.Sprite):
	def __init__(self, width, height):
		super().__init__() # sprite constructor
		self.image = pygame.Surface([width, height])
		self.rect = self.image.get_rect()

class Organism(Thread):
	def __init__(self, id, generation, initX, initY, maxHealth, habitat):
		Thread.__init__(self)
		self.color = BLACK
		self.sizeX = orgSize
		self.sizeY = orgSize
		self.generation = generation
		self.id = id
		self.posX = initX
		self.posY = initY
		self.velX = 1
		self.velY = 1
		self.habitat = habitat
		self.body = OrganismBody(self.sizeX, self.sizeY)
		self.health = maxHealth
		self.damageTaken = 0
		# self.brain = Brain()

	def update(self):

		# update health
		self.health -= naturalHealthDec + self.damageTaken
		self.damageTaken = 0
		self.color = (255 - (255 * ((self.health + 0.0)/initOrgHealth)), 255 - (255 * ((self.health + 0.0)/initOrgHealth)), 255 - (255 * ((self.health + 0.0)/initOrgHealth)))
		if self.health <= 0:
			return False # dead

		""" ** UPDATE SPRITE AFTER WHENEVER POS IS UPDATED ** """
		# update position
		self.posX += self.velX
		self.posY += self.velY

		# check collisions
		if self.posY > screensize[1]:
			self.posY = screensize[1]
		elif self.posY < 0:
			self.posY = 0
		if self.posX > screensize[0]:
			self.posY = screensize[0]
		elif self.posX < 0:
			self.posX = 0

		# update sprite
		self.body.rect.y = self.posY
		self.body.rect.x = self.posX

		# check for collision(s) with others. inefficient?
		for org in self.habitat.organisms:
			if org == self:
				continue
			if pygame.sprite.collide_rect(self.body, org.body):
				# collision. move away for now.
				self.posX += -1 * self.velX
				self.posY += -1 * self.velY

		# update sprite
		self.body.rect.y = self.posY
		self.body.rect.x = self.posX

		# random directions
		self.velX = random.choice([-1,1]) * random.randrange(3)
		self.velY = random.choice([-1,1]) * random.randrange(3)

		return True

	def run(self):
		while True:
			time.sleep(.1) # rest
			with habLock:
				if not self.update(): # death
					try:
						self.habitat.organisms.remove(self)
						print("organisms list with %d removed:" % self.id)
						for org in self.habitat.organisms:
							print("%d, " % org.id)
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

	# draw animals
	with habLock:
		for org in habitat.organisms:
			pygame.draw.rect(screen, org.color, [org.posX, org.posY, org.sizeX, org.sizeY])

	# draw food
	with habLock:
		for veg in habitat.vegs:
			pygame.draw.rect(screen, veg.color, [veg.posX, veg.posY, veg.sizeX, veg.sizeY])

	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 10 frames per second
	clock.tick(10)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()