#!/usr/bin/python
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.metrics import cm
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
import kivy.clock

import webbrowser
import pathlib
import threading
from schedule import Schedule
import time
import glob

import numpy as np
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
#matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')


try:
    client_file = glob.glob('../client_data/*.csv')[0]
# When ther is no such file the list is empty and we get index error,
# which we try to capture
except IndexError:
    client_file = str()

try:
    instructor_file = glob.glob('../instructor_data/*.csv')[0]
# When ther is no such file the list is empty and we get index error,
# which we try to capture
except IndexError:
    instructor_file = str()

# global variable
schedule_global = None


class MainWindow(Screen):
    pass




class Optimize(Screen):
    # TODO: co prodram ma zrobić po skończeniu optymalizacji
    # TODO: usunąć wywoływanie opt. w schedule.py
    # TODO: możliwość zmiany parametru greedy
    all_costs = list()
    def __init__(self, **kw):
        super().__init__(**kw)
        self.parameters = {
            'neighborhood_type_lst': list(),
            'initial_solution': False,
            'alpha': 0.5,
            'initial_temp': 100,
            'n_iter_one_temp': 50,
            'min_temp': 0.1,
            'epsilon': 0.01,
            'n_iter_without_improvement': 1000}

    def checkbox_click(self, instance, value, neighborhood_type):
        if value is True:
            self.parameters['neighborhood_type_lst'].append(neighborhood_type)
        else:
            self.parameters['neighborhood_type_lst'].remove(neighborhood_type)


    def on_text(self, parameter, input_parameter):
        try:
            self.parameters[parameter] = int(input_parameter)
        except ValueError:
            self.parameters[parameter] = 0

    def start_optimization(self):
        SM = Schedule(client_file=client_file,
                      instructor_file=instructor_file,
                      class_num=ScheduleParameters.schedule_parameters['class_num'],
                      day_num=ScheduleParameters.schedule_parameters['day_num'],
                      time_slot_num=ScheduleParameters.schedule_parameters['time_slot_num'],
                      max_clients_per_training=ScheduleParameters.schedule_parameters['max_clients_per_training'],
                      ticket_cost=ScheduleParameters.schedule_parameters['ticket_cost'],
                      hour_pay=ScheduleParameters.schedule_parameters['hour_pay'],
                      pay_for_presence=ScheduleParameters.schedule_parameters['pay_for_presence'],
                      class_renting_cost=ScheduleParameters.schedule_parameters['class_renting_cost'])
        SM.generate_random_schedule(greedy=False)

        print("\nINITIAL SCHEDULE")
        print(SM)
        print('Initial earnings: ', SM.get_cost())
        first_cost = SM.get_cost()
        tic = time.time()

        best_cost, num_of_iter, all_costs = SM.simulated_annealing(alpha=self.parameters['alpha'],
                                                                   initial_temp=self.parameters['initial_temp'],
                                                                   n_iter_one_temp=self.parameters['n_iter_one_temp'],
                                                                   min_temp=self.parameters['min_temp'],
                                                                   epsilon=self.parameters['epsilon'],
                                                                   n_iter_without_improvement=self.parameters['n_iter_without_improvement'],
                                                                   initial_solution=self.parameters['initial_solution'],
                                                                   neighborhood_type_lst=self.parameters['neighborhood_type_lst'])

        Optimize.all_costs = all_costs

        toc = time.time()

        print("\nAFTER OPTIMIZATION")
        print(SM)
        print("Number of iterations: ", num_of_iter)

        print("Best earnings: ", best_cost)
        second_cost = best_cost
        print("Time: ", toc - tic)

        SM.improve_results()
        print("\nIMPROVED SCHEDULE")
        print(SM)
        print("Best improved earnings: ", SM.get_cost())

        third_cost = SM.get_cost()

        print(f'{first_cost} $ --> {second_cost} $ --> {third_cost} $')
        global schedule_global
        schedule_global = SM

class ScheduleOptions(Screen):
    pass


class ClientFileChooser(Screen):
    def get_path(self):
        return str(pathlib.Path(__file__).parent.parent.resolve()) + r'\client_data'

    def selected(self, filename):
        global client_file
        try:
            self.ids.client_path_label.text = filename[0]
            client_file = filename[0]
        except:
            pass


class InstructorFileChooser(Screen):
    def get_path(self):
        return str(pathlib.Path(__file__).parent.parent.resolve()) + r'\instructor_data'

    def selected(self, filename):
        global instructor_file
        try:
            self.ids.instructor_path_label.text = filename[0]
            instructor_file = filename[0]
        except:
            pass


class ScheduleParameters(Screen):
    schedule_parameters = {
        'class_num': 1,
        'day_num': 6,
        'time_slot_num': 6,
        'max_clients_per_training': 5,
        'ticket_cost': 40,
        'hour_pay': 50,
        'pay_for_presence': 50,
        'class_renting_cost': 200}

    def on_text(self, parameter, input_parameter):
        try:
            ScheduleParameters.schedule_parameters[parameter] = int(input_parameter)
        except ValueError:
            ScheduleParameters.schedule_parameters[parameter] = 0
        print(ScheduleParameters.schedule_parameters['ticket_cost'])

class AboutOrganizer(Screen):
    def github_button_on(self):
        self.ids.github_button_img.source = 'images/GitHub-Mark-Light-120px-plus_pressed.png'

    def github_button_off(self):
        self.ids.github_button_img.source = 'images/GitHub-Mark-Light-120px-plus.png'
        webbrowser.open('https://github.com/kmotyka00/ScheduleOptimizationProblem')


# Functions to enable assignment
# self.font_size: self.width / 8
def set_font_size(font_size_divider, *args, **kwargs):
    def wrap(instance, value, *args, **kwargs):
        instance.font_size = value / font_size_divider
    return wrap


# self.text_size: self.size
def set_text_size(instance, value):
    instance.text_size = value


class SeeSchedule(Screen):
    classroom_displayed = 0

    def chceck_content(self, instance):
        # Lesson Content Popup
        if instance.ids['lesson'] is not None:
            participants = '\n'
            for participant in instance.ids['lesson'].participants:
                participants += str(participant) + '\n'
            lesson_content = f"Instructor ID: \n{str(instance.ids['lesson'].instructor)}" \
                             f"\n\nParticipants: {participants}"
        else:
            lesson_content = "That's a FREE REAL ESTATE"
        lesson_content_popup = Popup(title=f'Lesson information')
        popup_content = BoxLayout(orientation="vertical")
        label = Label(text=lesson_content, halign='center', valign='center')
        # self.font_size: self.width / 8
        label.bind(width=set_font_size(50))
        # self.text_size: self.size
        label.bind(size=set_text_size)
        popup_content.add_widget(label)
        popup_content.add_widget(Button(text='Close', size_hint=(1, 0.2), on_press=lesson_content_popup.dismiss))
        lesson_content_popup.content = popup_content
        return lesson_content_popup.open()


    def generate_see_schedule_layout(self):
        self.generate_schedule_layout()
        self.genrate_hours_layout()
        self.genrate_days_layout()

    def generate_schedule_layout(self):
        for time_slot in range(ScheduleParameters.schedule_parameters['day_num']
                               * ScheduleParameters.schedule_parameters['time_slot_num']):
            if f'Button{time_slot}' not in self.ids.keys():
                button = Button(text=f'{None}', halign='center', valign='center')
                button.background_normal = ''
                if time_slot % 2 == 0:
                    button.background_color = [.8, .8, .9, .6]
                else:
                    button.background_color = [.8, .8, .9, .8]
                # self.font_size: self.width / 8
                button.bind(width=set_font_size(8))
                # self.text_size: self.size
                button.bind(size=set_text_size)
                button.bind(on_press=self.chceck_content)
                button.ids['lesson'] = None
                button.ids['lesson_time_slot'] = None
                self.ids.schedule_layout.add_widget(button)
                self.ids[f'Button{time_slot}'] = button

    def genrate_hours_layout(self):
        for time_slot in range(ScheduleParameters.schedule_parameters['time_slot_num']):
            if f'Button_hours{time_slot}' not in self.ids.keys():
                button = Button(text=f'{time_slot}', halign='center', valign='center')
                button.background_normal = ''
                button.background_color = [.8, .8, .9, .2]
                # self.font_size: self.width / 8
                button.bind(width=set_font_size(8))
                # self.text_size: self.size
                button.bind(size=set_text_size)
                self.ids.hours_layout.add_widget(button)
                self.ids[f'Button_hours{time_slot}'] = button

    def genrate_days_layout(self):
        days = ['Monday', 'Tusday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in range(ScheduleParameters.schedule_parameters['day_num']):
            if f'Button_days{day}' not in self.ids.keys():
                button = Button(text=f'{days[day]}', halign='center', valign='center')
                button.background_normal = ''
                if day % 2 == 0:
                    button.background_color = [.8, .8, .9, .2]
                else:
                    button.background_color = [.8, .8, .9, .3]
                # self.font_size: self.width / 8
                button.bind(width=set_font_size(8))
                # self.text_size: self.size
                button.bind(size=set_text_size)
                self.ids.days_layout.add_widget(button)
                self.ids[f'Button_days{day}'] = button

    # Error Popup
    my_error_popup = Popup(title="Error", size_hint=(None, None), size=(300, 200), auto_dismiss=False)
    error_popup_content = BoxLayout(orientation="vertical")
    error_popup_content.add_widget(
        Label(size=(cm(6), cm(4)), pos_hint={'top': 1}, text_size=(cm(6), cm(4)), font_size='20sp',
              text='AttributeError: Error during updating schedule - schedule is empty.',
              halign='center', valign='center'))
    error_popup_content.add_widget(Button(text='Close', size_hint=(1, 0.2), on_press=my_error_popup.dismiss))
    my_error_popup.content = error_popup_content

    def update_schedule_description(self):
        # TODO zmienić 36, na coś wczytanego
        try:
            global schedule_global
            # reshape and transpose schedule for convenient indexing
            temp_schedule = schedule_global.schedule[SeeSchedule.classroom_displayed].T.reshape(-1, 1, 1).squeeze()
            for time_slot in range(ScheduleParameters.schedule_parameters['day_num']
                               * ScheduleParameters.schedule_parameters['time_slot_num']):
                lesson = temp_schedule[time_slot]
                if lesson != None:
                    # Read lesson_type and convert it to user friendly string
                    new_text = f'{lesson.lesson_type}'.split('.')[1].split('_')
                    converted_text = str()
                    for i in range(len(new_text)):
                        converted_text += new_text[i] + ' '
                    # make button kind of a parent for lesson
                    self.ids[f'Button{time_slot}'].ids['lesson'] = lesson
                    self.ids[f'Button{time_slot}'].ids['lesson_time_slot'] = \
                        time_slot
                    self.ids[f'Button{time_slot}'].text = converted_text
                else:
                    self.ids[f'Button{time_slot}'].ids['lesson'] = lesson
                    self.ids[f'Button{time_slot}'].ids['lesson_time_slot'] = \
                        time_slot
                    self.ids[f'Button{time_slot}'].text = 'Free'
        except AttributeError:
            SeeSchedule.my_error_popup.open()

    def change_displayed_class_button_on_press(self, instance):
        SeeSchedule.classroom_displayed = instance.ids['classroom_id']
        self.update_schedule_description()

    # Pick Classroom Popup
    def pick_classroom_popup(self):
        pick_classroom_popup = Popup(title="Error", size_hint=(0.6, 0.6), auto_dismiss=False)
        pick_classroom_popup_main_layout = GridLayout(cols=1, size_hint=(1, 1))
        pick_classroom_popup_classroom_buttons = GridLayout(cols=3, size_hint=(1, 0.8))
        for classroom in range(ScheduleParameters.schedule_parameters['class_num']):
            button = ToggleButton(group='classroom_displayed', text=f'Classroom:{classroom}', halign='center', valign='center')
            button.ids['classroom_id'] = classroom
            # self.font_size: self.width / 8
            button.bind(width=set_font_size(12))
            # self.text_size: self.size
            button.bind(size=set_text_size)
            button.bind(on_press=self.change_displayed_class_button_on_press)
            pick_classroom_popup_classroom_buttons.add_widget(button)

        pick_classroom_popup_main_layout.add_widget(pick_classroom_popup_classroom_buttons)
        pick_classroom_popup_main_layout.add_widget(Button(text='Close', size_hint=(1, 0.2),
                                                       on_press=pick_classroom_popup.dismiss))

        pick_classroom_popup.content = pick_classroom_popup_main_layout
        pick_classroom_popup.open()





class GoalFunction(Screen):
    box = None
    def draw_plot(self):
        box = self.ids.box
        box.clear_widgets()
        plt.clf()
        plt.plot(Optimize.all_costs)
        plt.title('Goal function over number of iterations')
        plt.xlabel('Number of iterations')
        plt.ylabel('Earnings [$]')
        box.add_widget(FigureCanvasKivyAgg(plt.gcf()))


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file('new_window.kv')

class ScheduleOrganizer(App):
    def build(self):
        return kv


if __name__ == '__main__':
    ScheduleOrganizer().run()

#TODO: Wyświetlanie wyników, wykresu
#TODO explicity