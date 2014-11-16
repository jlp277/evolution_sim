"""
 Show how to use a sprite backed by a graphic.
 
 Sample Python/Pygame Programs
 Simpson College Computer Science
 http://programarcadegames.com/
 http://simpson.edu/computer-science/
 
 Explanation video: http://youtu.be/vRB_983kUMc
"""
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
 
pygame.display.set_caption("My Game")
 
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
		self.organisms = []
		for id in range(20):
			x = random.randrange(screensize[0])
			y = random.randrange(screensize[1])
			organism = Organism(id, 0, x, y)
			organism.start()
			self.organisms.append(organism)

	def run(self):
		while True:
			# grow food and shit
			pass

class Organism(Thread):
	def __init__(self, id, generation, initX, initY):
		Thread.__init__(self)
		self.color = BLACK
		self.sizeX = 5
		self.sizeY = 5
		self.generation = generation
		self.id = id
		self.posX = initX
		self.posY = initY
		self.velX = 1
		self.velY = 1
		# self.health = maxHealth
		# self.brain = Brain()

	def update(self):
		# update health
		# self.health -= 1
		# update position
		# Bounce the rectangle if needed
		self.posX += self.velX
		self.posY += self.velY

		if self.posY > screensize[1]:
		    self.posY = screensize[1]
		elif self.posY < 0:
			self.posY = 0
		if self.posX > screensize[0]:
		    self.posY = screensize[0]
		elif self.posX < 0:
			self.posX = 0

		# random directions
		self.velX = random.choice([-1,1]) * random.randrange(2)
		self.velY = random.choice([-1,1]) * random.randrange(2)

	def run(self):
		while True:
			time.sleep(.01)
			with orgLock:
				self.update()

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
			pygame.draw.rect(screen, BLACK, [org.posX, org.posY, org.sizeX, org.sizeY])
 
	# --- Go ahead and update the screen with what we've drawn.
	pygame.display.flip()
 
	# --- Limit to 60 frames per second
	clock.tick(60)
 
# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()