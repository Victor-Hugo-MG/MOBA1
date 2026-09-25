import cave
import cave.event
import cave.math

# Use an Entity Property called "value" to access and/or modify the current value.


class UIInputSliderComponent(cave.Component):
	textFormat = "%d%%"

	def start(self, scene: cave.Scene):
		self.ui : cave.UIElementComponent = self.entity.get("UI Element")
		self.barUI : cave.UIElementComponent = self.entity.getChild("Bar").get("UI Element")
		self.textUI : cave.UIElementComponent = self.entity.getChild("Text").get("UI Element")

		if not "value" in self.entity.properties:
			self.entity.properties["value"] = 0.5

	def update(self):
		if self.ui.isPressed():
			mousePos = cave.getMousePositionUI()
			rect  = self.ui.getRect()

			val = cave.math.mapRange(mousePos.x + 0.5, rect.left, rect.right, 0.0, 1.0)
			val = cave.math.clamp(val, 0.0, 1.0)
			self.barUI.scale.setRelativeX(val)

		self.entity.properties["value"] = self.barUI.scale.getRelative().x
		self.textUI.setText(self.textFormat % (self.entity.properties["value"] * 100))
		
	def end(self, scene: cave.Scene):
		pass


class UIInputNumberComponent(cave.Component):
	textFormat = "%.2f"
	stepValue = 10.0

	def start(self, scene: cave.Scene):
		self.ui : cave.UIElementComponent = self.entity.get("UI Element")

		self._lastPosX = None
		self._dragging = False

		if not "value" in self.entity.properties:
			self.entity.properties["value"] = 0.0

	def update(self):
		if self.ui.isPressed():
			self._dragging = True
			
		if self._dragging:
			if not cave.getEvents().active(cave.event.MOUSE_LEFT):
				self._dragging = False

			mousePos = cave.getMousePositionUI()
			
			if self._lastPosX != None:
				amount = mousePos.x - self._lastPosX
				self.entity.properties["value"] += self.stepValue * amount
			self._lastPosX = mousePos.x
		else:
			self._lastPosX = None

		self.ui.setText(self.textFormat % self.entity.properties["value"])
		
	def end(self, scene: cave.Scene):
		pass


class UIInputTextComponent(cave.Component):
	def start(self, scene: cave.Scene):
		self.ui : cave.UIElementComponent = self.entity.get("UI Element")

		self._isEditing = False

		style = self.getStyle()

		self.normalColor  = cave.UIStyleColor(style.colorBase)
		self.editingColor = cave.UIStyleColor(style.colorPressed)

		if not "value" in self.entity.properties:
			self.entity.properties["value"] = ""

	def getStyle(self) -> cave.UIStyle:
		style = self.ui.quad.styleOverride.get(False)
		if style is None:
			style = self.ui.quad.style
		return style

	def update(self):
		events = cave.getEvents()
		style = self.getStyle()

		if self.ui.isPressed():
			self._isEditing = True
			style.colorBase = cave.UIStyleColor(self.editingColor)
			
		if self._isEditing:
			if events.pressed(cave.event.MOUSE_LEFT) and not self.ui.isHovered():
				self._isEditing = False
				style.colorBase = cave.UIStyleColor(self.normalColor)
			
			self.entity.properties["value"] += events.getTextInput()
			if events.pressed(cave.event.KEY_BACKSPACE):
				self.entity.properties["value"] = self.entity.properties["value"][:-1]

		self.ui.setText(self.entity.properties["value"])
		
	def end(self, scene: cave.Scene):
		pass


class PauseComponent(cave.Component):
	def start(self, scene: cave.Scene):
		self.menuPause = self.entity.getChild("Menu Pause")

	def update(self):
		events = cave.getEvents()
		scene  = self.entity.getScene()

		if events.released(cave.event.KEY_ESCAPE):
			scene.paused = True
			self.menuPause.activate(scene)
			cave.showMouse(True)
			events.setRelativeMouse(False)

	def pausedUpdate(self):
		events = cave.getEvents()
		scene  = self.entity.getScene()
		
		cave.showMouse(True)
		events.setRelativeMouse(False)

		if events.released(cave.event.KEY_ESCAPE):
			scene.paused = False
			self.menuPause.deactivate(scene)

	def end(self, scene: cave.Scene):
		pass


