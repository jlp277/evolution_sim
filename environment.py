import pygame
import random
from threading import *
import time

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

orgLock = Lock()
orgCond = Condition(orgLock)

class Habitat(Thread):
	def __init__(self):
		Thread.__init__(self)
		# self.organisms = pygame.sprite.Group()
		self.organisms = []
		for id in range(20):
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			organism = Organism(id, 0, x, y, self)
			organism.start()
			# organism.body.add(self.organisms)
			self.organisms.append(organism)

	def run(self):
		while True:
			# grow food and shit
			pass

class OrganismBody(pygame.sprite.Sprite):
	def __init__(self, color, width, height):
		super().__init__() # sprite constructor
		self.image = pygame.Surface([width, height])
		# self.image.fill(color)
		self.rect = self.image.get_rect()

class Organism(Thread):
	def __init__(self, id, generation, initX, initY, habitat):
		Thread.__init__(self)
		self.color = BLACK
		self.sizeX = 10
		self.sizeY = 10
		self.generation = generation
		self.id = id
		self.posX = initX
		self.posY = initY
		self.velX = 1
		self.velY = 1
		self.habitat = habitat
		self.body = OrganismBody(self.color, self.sizeX, self.sizeY)
		# self.health = maxHealth
		# self.brain = Brain()

	def update(self):
		global orgLock
		# update health
		# self.health -= 1
		# update position
		# Bounce the rectangle if needed
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

		for org in self.habitat.organisms:
			# check for collision(s) with others
			if org == self:
				continue
			if pygame.sprite.collide_rect(self.body, org.body):
				# collision. move away.
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
			time.sleep(.01)
			with orgLock:
				if not self.update():
					break # death

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

	for org in habitat.organisms:
		with orgLock:
			pygame.draw.rect(screen, org.color, [org.posX, org.posY, org.sizeX, org.sizeY])
 
	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 60 frames per second
	clock.tick(60)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()