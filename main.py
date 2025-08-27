# File: main.py
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.core.window import Window
import socketio
import requests

# --- Configuration ---
# IMPORTANT: Remember to use your server's correct local IP address.
# This must be the IP of the computer running your server.py, and both
# your computer and phone must be on the same Wi-Fi network.
BACKEND_URL = 'http://192.168.1.100:5000'
SIO = socketio.Client()
Window.clearcolor = (0.05, 0.07, 0.1, 1) # A deep navy blue background

# --- Custom Data Label Widget ---
class DataLabel(BoxLayout):
    def __init__(self, node_id, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.height = 45
        self.width = 180
        self.padding = (10, 0)
        self.spacing = 5

        with self.canvas.before:
            Color(0.2, 0.4, 0.9, 0.75)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0.7, 0.8, 1, 0.9)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 8), width=1.5)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

        self.icon = Image(source='assets/icons/thermometer.png', size_hint_x=0.35)
        self.value_label = Label(text="N/A", font_size='18sp', bold=True)

        self.add_widget(self.icon)
        self.add_widget(self.value_label)

        # Schedule the registration of this widget to the main app.
        # This is a robust way to ensure the app is fully running before
        # trying to access its properties.
        def register_widget(*args):
            app = App.get_running_app()
            if app: # Check if the app is running before registering
                app.register_label(node_id, self.value_label)

        Clock.schedule_once(register_widget)

    def _update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, 8)

# --- Kivy App Screens ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        layout.add_widget(Label(text='Plant Pulse Login', font_size='24sp'))
        self.username = TextInput(hint_text='Username', multiline=False, size_hint_y=None, height=44)
        self.password = TextInput(hint_text='Password', password=True, multiline=False, size_hint_y=None, height=44)
        self.message = Label(text='', color=(1, 0, 0, 1))
        login_button = Button(text='Login', size_hint_y=None, height=50)
        login_button.bind(on_press=self.login)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_button)
        layout.add_widget(self.message)
        self.add_widget(layout)

    def login(self, instance):
        username = self.username.text.strip()
        password = self.password.text.strip()
        try:
            response = requests.post(
                f"{BACKEND_URL}/login",
                json={'username': username, 'password': password},
                timeout=5
            )
            if response.status_code == 200:
                self.message.text = ''
                self.manager.current = 'dashboard'
            else:
                self.message.text = 'Invalid credentials. Please try again.'
        except requests.exceptions.ConnectionError:
            self.message.text = 'Could not connect to the server.'
        except Exception as e:
            self.message.text = f'An error occurred: {e}'

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()
        main_layout.add_widget(Image(
            source='assets/dashboard_background.png',
            allow_stretch=True,
            keep_ratio=False
        ))
        bottom_bar = BoxLayout(
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0},
            padding=5,
            spacing=5
        )
        plant_sections = {
            "crusher": "CRUSHER",
            "kiln": "KILN",
            "cement_mill": "C. MILL",
        }
        for screen_name, display_text in plant_sections.items():
            btn = Button(text=display_text, font_size='14sp')
            btn.bind(on_press=self.go_to_section)
            btn.screen_name = screen_name
            bottom_bar.add_widget(btn)
        main_layout.add_widget(bottom_bar)
        self.add_widget(main_layout)

    def go_to_section(self, instance):
        self.manager.current = instance.screen_name

class SectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.background_image = Image(source='', allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.background_image)
        back_button = Button(text="< Dashboard", size_hint=(0.25, 0.08), pos_hint={'x': 0.02, 'y': 0.90})
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        self.layout.add_widget(back_button)
        self.add_widget(self.layout)

class CrusherScreen(SectionScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_image.source = 'assets/mimics/crusher.png'

class KilnScreen(SectionScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_image.source = 'assets/mimics/kiln.png'

        # Position for Kiln Feed End Temperature
        label1 = DataLabel(node_id='KILN_FEED_END_TEMP', pos_hint={'center_x': 0.2, 'center_y': 0.45})
        label1.icon.source = 'assets/icons/thermometer.png'
        self.layout.add_widget(label1)

        # Position for Preheater Exit Temperature (Burning Zone)
        label2 = DataLabel(node_id='PREHEATER_EXIT_TEMP', pos_hint={'center_x': 0.5, 'center_y': 0.65})
        label2.icon.source = 'assets/icons/thermometer.png'
        self.layout.add_widget(label2)

        # Position for Clinker Production Rate
        label3 = DataLabel(node_id='CLINKER_TONS_PER_HOUR', pos_hint={'center_x': 0.8, 'center_y': 0.55})
        label3.icon.source = 'assets/icons/weight.png'
        self.layout.add_widget(label3)

        # Position for Cooler Exit Temperature
        label4 = DataLabel(node_id='COOLER_EXIT_TEMP', pos_hint={'center_x': 0.8, 'center_y': 0.75})
        label4.icon.source = 'assets/icons/thermometer.png'
        self.layout.add_widget(label4)

class CementMillScreen(SectionScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_image.source = 'assets/mimics/cement_mill.png'

# --- The Main Application Class ---
class PlantApp(App):
    def build(self):
        self.registered_labels = {}
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CrusherScreen(name='crusher'))
        sm.add_widget(KilnScreen(name='kiln'))
        sm.add_widget(CementMillScreen(name='cement_mill'))
        self.setup_socketio_events()
        return sm

    def on_start(self):
        # Connect to WebSocket when entering the dashboard
        def on_screen_change(instance, current_screen_name):
            if current_screen_name == 'dashboard' and not SIO.connected:
                try:
                    SIO.connect(BACKEND_URL)
                except Exception as e:
                    print(f"Failed to connect to WebSocket: {e}")
        self.root.bind(current=on_screen_change)

    def register_label(self, node_id, label_widget):
        self.registered_labels[node_id] = label_widget

    def update_label_text(self, label, text):
        label.text = text

    def setup_socketio_events(self):
        @SIO.event
        def connect():
            print("Successfully connected to WebSocket server.")

        @SIO.event
        def plant_data_update(data):
            print(f"KIVY APP RECEIVED DATA: {data}")
            node_name = data.get('name')
            value = data.get('value')
            units = {
                "PREHEATER_EXIT_TEMP": "°C",
                "KILN_FEED_END_TEMP": "°C",
                "COOLER_EXIT_TEMP": "°C",
                "CLINKER_TONS_PER_HOUR": "t/h",
            }
            unit_str = units.get(node_name, "")
            if node_name in self.registered_labels:
                label_to_update = self.registered_labels[node_name]
                # Use Kivy's markup for bold text
                display_text = f"[b]{value}[/b] {unit_str}"
                label_to_update.markup = True # Enable markup
                # Schedule the UI update on the main Kivy thread
                Clock.schedule_once(lambda dt: self.update_label_text(label_to_update, display_text))

        @SIO.event
        def disconnect():
            print("Disconnected from WebSocket server.")

if __name__ == '__main__':
    PlantApp().run()