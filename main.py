import numpy as np
import pandas as pd
from typing import List
from enum import Enum
import copy
import random
import time


class LessonType(Enum):
    """ 
    Class enumerating lesson types,
    enumeration numbers are important,
    because they are used in a questionnaire for customers 
    """
    CELLULITE_KILLER = 0
    ZUMBA = 1
    ZUMBA_ADVANCED = 2
    FITNESS = 3
    CROSSFIT = 4
    BRAZILIAN_BUTT = 5
    PILATES = 6
    CITY_PUMP = 7
    STRETCHING = 8
    YOGA = 9


class Client:
    '''
    A class used to represent a Client

    ...
    Atributes
    ---------
    id : int
        a number which represents the client 
    selected_training: List[LessonType]
        list of the trainings selected by a client

    Methods
    -------
    __str__()
        Helps to print information about the client prettier and cleaner
    '''
    def __init__(self, id: int, selected_training: List[LessonType] = None):
        self.id = id
        if selected_training is None:
            self.selected_training = np.array(list())
        else:
            self.selected_training = np.array(selected_training)

    def __str__(self) -> str:
        return f"id: {self.id}, selected_training: {self.selected_training}"


class Instructor:
    '''
    A class used to represent an Instructor

    ...
    Atributes
    ---------
    id : int
        a number which represents the instructor 
    qualifications: List[LessonType]
        list of the trainings which can be tought by the instructor

    Methods
    -------
    __str__()
        Helps to print information about the instructor prettier and cleaner
    '''
    def __init__(self, id, qualifications: List[LessonType] = None):
        self.id = id
        if qualifications is None:
            self.qualifications = np.array(list())
        else:
            self.qualifications = np.array(qualifications)

    def __str__(self) -> str:
        return f"id: {self.id}, qualifications: {self.qualifications}"


class Lesson:
    '''
    A class used to represent a Lesson

    ...
    Atributes
    ---------
    instructor : Instructor
        an instructor which conducts classes
    lesson_type: LessonType
        type of the conducted classes
    participiants: List[Client]
        a list of clients which take part in the classes

    Methods
    -------
    __str__()
        Helps to print information about the lesson prettier and cleaner
    '''
    def __init__(self, instructor: Instructor, lesson_type: LessonType, participants: List[Client] = None):
        self.instructor = instructor
        self.lesson_type = lesson_type
        if participants is None:
            self.participants = np.array(list())
        else:
            self.participants = np.array(participants)

    def __str__(self):
        lesson_type = str(self.lesson_type)
        lt = lesson_type.split(sep='.')
        lesson_type = lt[1]
        return f"I: {self.instructor.id}, L: {lesson_type}"


class Schedule:
    '''
    A class used to represent our Schedule 

    ...
    Atributes
    ---------
    client_file : str
        the path to the file which contains information about the trainings selected by
        clients (ids of the clients and selected training stored in a *.csv file)
    instructor_file: str
        the path to the file which contains information about the qualifications and ids
        of the instructors stored in the *.csv file
    class_num: int
        the number of classrooms in the building
    day_num: int
        the number of days on which the classes are held
    time_slot_num: int
        the number of time slots during a day on which the classes are held
    max_clients_per_training: int
        maximum number of clients which can participate in the classes
    ticket_cost: int
        cost of a class ticket
    hour_pay: int
        instructor's hour pay
    pay_for_presence: int
        amount of money which instructor revieves for coming to the workplace
    class_renting_cost: int 
        cost of renting a class (per day)

    Methods
    -------
    generate_random_schedule(greedy=False)
        Based on parameters of our schedule generate random schedule
    get_cost(current_solution=None)
        Calculate cost of classes for a current schedule
    get_neighbor(current_solution)
        Move one lesson from current schedule to different timeslot
    simulated_annealing(self, alpha=0.9999, initial_temp=1000, n_iter_one_temp=50, min_temp=0.1,
                        epsilon=0.01, n_iter_without_improvement=1000, initial_solution=True)
        Simulated Annealing algorithm which optimizes arranging of a schedule
    improve_results()
        Minimizes days of presence for each instructor
    __str__()
        Helps to print a current schedule preety and intuitive
    '''
    def __init__(self, client_file: str = 'form_answers.csv', instructor_file: str = 'instructors_info.csv',
                 class_num=1, day_num=6, time_slot_num=6, max_clients_per_training=5,
                 ticket_cost=40, hour_pay=50, pay_for_presence=50, class_renting_cost=200):

        self.class_id = class_num
        self.day = day_num  # monday - saturday
        self.time_slot = time_slot_num
        self.max_clients_per_training = max_clients_per_training

        self.clients = list()
        df = pd.read_csv(client_file, sep=";")
        for index, client in df.iterrows():
            self.clients.append(Client(client['Client_ID'],
                                       [LessonType(int(elem)) for elem in client['Lesson_Types'].split(sep=" ")]))
        self.clients = np.array(self.clients)

        self.instructors = list()
        df = pd.read_csv(instructor_file, sep=";")
        for index, instructor in df.iterrows():
            self.instructors.append(Instructor(instructor['Instructor_ID'],
                                               [LessonType(int(elem)) for elem in
                                                instructor['Lesson_Types'].split(sep=" ")]))
        self.instructors = np.array(self.instructors) #  lista na początku żeby móc appendować na essie
        self.schedule = np.array([None for x in
                                  range(self.class_id * self.day * self.time_slot)])
        self.schedule = self.schedule.reshape((self.class_id, self.day, self.time_slot))

        # economy
        self.ticket_cost = ticket_cost
        self.hour_pay = hour_pay
        self.pay_for_presence = pay_for_presence
        self.class_renting_cost = class_renting_cost

    def generate_random_schedule(self, greedy=False):

        self.schedule = self.schedule.reshape((-1, 1))  # temp reshaping for easier indexing
        i = 0
        free_ts = list(np.arange(self.schedule.shape[0]))
        for lesson_type in LessonType:
            all_participants = [client for client in self.clients if lesson_type in client.selected_training]
            all_instructors = [instructor for instructor in self.instructors if
                               lesson_type in instructor.qualifications]
            num_of_trainings = int(np.ceil(len(all_participants) / self.max_clients_per_training))
            for training in range(num_of_trainings):
                participants = all_participants[training * self.max_clients_per_training:
                                                training * self.max_clients_per_training + self.max_clients_per_training]
                if greedy:
                    lesson_id = i
                    i += 1
                else:
                    lesson_id = free_ts.pop(random.randint(0, len(free_ts) - 1))

                interval = self.day * self.time_slot
                for ts in range(lesson_id % interval, self.schedule.shape[0], interval):
                    if self.schedule[ts] != None:
                        all_instructors.remove(self.schedule[ts].instructor.id)  # TODO: TEST

                instructor = random.choice(all_instructors)
                self.schedule[lesson_id] = Lesson(instructor, lesson_type, participants)

        self.schedule = self.schedule.reshape((self.class_id, self.day, self.time_slot))

    def get_cost(self, current_solution=None):
        # dla każdej komórki w current_solution policzyć liczbę uczestników,
        # pomnożyć przez cenę zajęć,
        # odjąć koszt przyjścia trenera w danym dniu
        # i odjąć koszt wynajęcia sali w danym dniu

        if current_solution is None:
            current_solution = self.schedule

        participants_sum = 0
        instructors_hours = np.zeros(shape=(self.instructors.shape[0], self.day))
        class_per_day = np.zeros(shape=(self.class_id, self.day))

        for c in range(current_solution.shape[0]):
            for d in range(current_solution.shape[1]):
                for ts in range(current_solution.shape[2]):
                    if current_solution[c, d, ts] is not None:
                        participants_sum += current_solution[c, d, ts].participants.shape[0]
                        instructors_hours[current_solution[c, d, ts].instructor.id, d] += 1
                        class_per_day[c, d] = 1

        return self.ticket_cost * participants_sum - \
               self.hour_pay * instructors_hours.sum() - \
               self.pay_for_presence * (instructors_hours > 0).sum() - \
               self.class_renting_cost * class_per_day.sum()

    def get_neighbor(self, current_solution):

        not_none_id_list = np.argwhere(current_solution != None)
        random_not_none_id = tuple(random.choice(not_none_id_list))

        none_id_list = np.argwhere(current_solution == None)
        random_none_id = tuple(random.choice(none_id_list))

        current_solution[random_none_id] = current_solution[random_not_none_id]
        current_solution[random_not_none_id] = None
        return current_solution

    def simulated_annealing(self, alpha=0.9999, initial_temp=1000, n_iter_one_temp=50, min_temp=0.1,
                            epsilon=0.01, n_iter_without_improvement=1000, initial_solution=True):

        if not initial_solution:
            self.generate_random_schedule()  # self.schedule initialized

        current_solution = copy.deepcopy(self.schedule)
        best_solution = copy.deepcopy(current_solution)

        current_temp = initial_temp

        current_cost = self.get_cost(current_solution)
        best_cost = self.get_cost(best_solution)

        counter = 0
        total_counter = 0

        while current_temp > min_temp and counter < n_iter_without_improvement:
            for j in range(0, n_iter_one_temp):
                total_counter += 1
                neighbor_solution = self.get_neighbor(current_solution)
                neighbor_cost = self.get_cost(neighbor_solution)
                delta = neighbor_cost - current_cost
                if delta >= 0:
                    current_solution = neighbor_solution
                    current_cost = neighbor_cost
                    if current_cost > best_cost:
                        best_solution = copy.deepcopy(current_solution)
                        best_cost = current_cost
                else:
                    s = random.uniform(0, 1)
                    if s < np.exp(delta/current_temp):
                        current_solution = neighbor_solution
                        current_cost = neighbor_cost

            current_temp = alpha * current_temp

            if (abs(current_cost - best_cost)) < epsilon:
                counter += 1
            else:
                counter = 0

        self.schedule = best_solution
        return best_cost, total_counter


    def improve_results(self):

        changed = True
        while changed:
            changed = False
            for instructor in self.instructors:
                trainings = list()
                for c in range(self.schedule.shape[0]):
                    for d in range(self.schedule.shape[1]):
                        timeslots = list()
                        free_ts = list()
                        for ts in range(self.schedule.shape[2]):
                            if self.schedule[c, d, ts] != None:
                                if self.schedule[c, d, ts].instructor.id == instructor.id:
                                    timeslots.append(ts)
                            else:
                                free_ts.append(ts)
                        if len(timeslots) > 0:
                            trainings.append([d, timeslots, free_ts])

                    trainings2 = [v for v in sorted(trainings, key=lambda item: len(item[1]))]
                    for i in range(len(trainings2) - 1):
                        for j in range(i+1, len(trainings2)):
                            timeslots_taken = list()
                            changed = False
                            if len(trainings2[i][1]) <= len(trainings2[j][2]):
                                for ts_iter in range(len(trainings2[i][1])):
                                    self.schedule[c, trainings2[j][0], trainings2[j][2][ts_iter]] = \
                                        self.schedule[c, trainings2[i][0], trainings2[i][1][ts_iter]]

                                    self.schedule[c, trainings2[i][0], trainings2[i][1][ts_iter]] = None
                                    # dodaj do zajętych w j
                                    trainings2[j][1].append(trainings2[j][2][ts_iter])
                                    # dodaj do zwolnionych w i
                                    trainings2[i][2].append(trainings2[i][1][ts_iter])
                                    # zapamiętaj do usunięcia z wolnych w j
                                    timeslots_taken.append(trainings2[j][2][ts_iter])

                                    # zmienna po to aby po wrzuceniu i do j nie sprawdzać dalszych j
                                    changed = True

                                # usuń zapamiętane
                                for ts_iter in timeslots_taken:
                                    trainings2[j][2].remove(ts_iter)
                                # wyczyść listę zajętych dla i
                                trainings2[i][1] = []

                            elif len(trainings2[i][2]) > len(trainings2[j][1]):
                                for ts_iter in range(len(trainings2[j][1])):
                                    self.schedule[c, trainings2[i][0], trainings2[i][2][ts_iter]] = \
                                        self.schedule[c, trainings2[j][0], trainings2[j][1][ts_iter]]

                                    self.schedule[c, trainings2[j][0], trainings2[j][1][ts_iter]] = None
                                    # zmienna po to aby po wrzuceniu i do j nie sprawdzać dalszych j
                                    changed = True
                                    # dodaj do zajętych w i
                                    trainings2[i][1].append(trainings2[i][2][ts_iter])
                                    # dodaj do zwolnionych w j
                                    trainings2[j][2].append(trainings2[j][1][ts_iter])
                                    # zapamiętaj do usunięcia z wolnych w i
                                    timeslots_taken.append(trainings2[i][2][ts_iter])

                                    # zmienna po to aby po wrzuceniu j do i nie sprawdzać dalszych j
                                    changed = True

                                # usuń zapamiętane
                                for ts_iter in timeslots_taken:
                                    trainings2[i][2].remove(ts_iter)
                                    # wyczyść listę zajętych dla i
                                trainings2[j][1] = []

                            if changed:
                                # aby utrzymać właściwą kolejność
                                trainings2 = [v for v in sorted(trainings, key=lambda item: len(item[1]))]
                                # przejdź do kolejnej iteracji dla i
                                break
     
    def __str__(self):

        result = str()
        days = ["----- MONDAY -----", "----- TUESDAY -----", "----- WEDNESDAY -----", "----- THURSDAY -----",
                "----- FRIDAY -----", "----- SATURDAY -----"]
        hour = ["16:00 - 17:00", "17:00 - 18:00", "18:00 - 19:00", "19:00 - 20:00", "20:00 - 21:00", "21:00 - 22:00"]
        for c in range(self.schedule.shape[0]):
            for d in range(self.schedule.shape[1]):
                result += "\n" + days[d] + "\n\n"
                for ts in range(self.schedule.shape[2]):
                    result += hour[ts] + "\t"
                    if self.schedule[c, d, ts] is None:
                        result += "Free\n"
                    else:
                        result += str(self.schedule[c, d, ts]) + "\n"

        return result

SM = Schedule(max_clients_per_training=5, time_slot_num=6)
SM.generate_random_schedule(greedy=False)

print("\nINITIAL SCHEDULE")
print(SM)
print('Initial earnings: ', SM.get_cost())

tic = time.time()
best_cost, num_of_iter = SM.simulated_annealing(alpha=0.9999, initial_temp=1000, n_iter_one_temp=50, min_temp=0.1,
                                                epsilon=0.01, n_iter_without_improvement=1000, initial_solution=True)
toc = time.time()

print("\nAFTER OPTIMIZATION")
print(SM)
print("Number of iterations: ", num_of_iter)
print("Best earnings: ", best_cost)
print("Time: ", toc-tic)

SM.improve_results()
print("\nIMPROVED SCHEDULE")
print(SM)
print("Best improved earnings: ", SM.get_cost())

#  TODO: - zwiększyć liczbę klas
#  TODO: - poprawienie rozwiązania podczas działania algorytmu SA (przenoszenie względem prowadzących)
#  TODO: - dodanie listy kompetencji i mniej losowe przydzielanie prowadzących do zajęć (może jako prawdopodobieństwo)
#  TODO: - ograniczenia - chwiliowo pomijamy ograniczenie 6) i 7)
#  TODO: - z 7) można zrobić tak, że po ułożeniu już planu sprawdzamy dla każdego użytkownika ile razy w tygodniu
#   trenuje i jeśli jego liczba treningów jest większa niż max to przenosimy go do innej grupy. Można założyć na
#   początku działania algorytmu limit np. 12 (zamiast 10) żeby mieć jakieś pole manewru. Takie podejście może
#   okazać się lepsze bo nie utrudnia działania algorytmu a takich przypadków nie powinno być dużo
#  TODO: - inaczej wybierać otoczenie
#  TODO: - dodać dokumentację
