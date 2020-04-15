#!/usr/bin/env python3

import random
from person import Person
from contact_graph import Contact_Graph
import sys
from contact_distribution import world_pdf


class SIR_Graph(Contact_Graph):
    def __init__(
        self,
        p,
        contact_distribution,
        n=0,
        file_name=None,
        p_initial=None,
        initial_infected=1,
        recovery_time=14,
        t=None,
        a=0,
        b=1,
        mechanisms=set(),
        quarantine_probability=0,
        contact_threshold=0,
    ):
        super().__init__(
            contact_distribution=contact_distribution,
            n=n,
            file_name=file_name,
            t=t,
            a=a,
            b=b,
        )
        self.p = p
        if p_initial is not None:
            self.p_initial = p_initial
            self.patient_zero = None
        else:
            self.patient_zero = set(
                random.sample(list(range(self.size)), k=initial_infected)
            )

        self.recovery_time = recovery_time
        self.quarantine_probability = quarantine_probability
        self.contact_threshold = contact_threshold
        self.random_quarantine = "random quarantine" in mechanisms
        self.scheduled_quarantine = "scheduled quarantine" in mechanisms
        self.symptomatic_quarantine = "symptomatic quarantine" in mechanisms
        self.high_contact_targeting = "high-contact targeting" in mechanisms

        self.current_time = 0

        self.number_suspectible = n
        self.number_infected = 0
        self.number_recovered = 0

        self.susceptible = set([person for person in self.people])
        self.infected = set()
        self.recovered = set()

        self.groups = [set() for _ in range(5)]

        while self.number_infected == 0:
            for person in self.people:
                infected = False
                if p_initial is not None:
                    infected = random.uniform(0, 1) <= self.p_initial
                else:
                    infected = person.id in self.patient_zero
                if infected:
                    person.becomes_infected(self.current_time)
                    self.infected.add(person)
                    self.susceptible.remove(person)
                    self.number_infected += 1
                    self.number_suspectible -= 1
                self.groups[person.group_number].add(person)
        if self.random_quarantine:
            for person in self.people:
                if random.uniform(0, 1) <= self.quarantine_probability:
                    person.quarantines()
        self.number_of_new_cases = [self.number_infected]

    def round(self):
        if self.scheduled_quarantine:
            group_number = self.time % 5
            for person in self.groups[group_number]:
                person.quarantines()
            for person in self.groups[group_number - 1]:
                person.unquarantines()
        infected_this_round = set()
        recovers_this_round = set()
        for person in self.infected:
            if self.current_time - person.infection_time >= self.recovery_time:
                recovers_this_round.add(person)
            for contact in person.contacts:
                if self.transmission(person, contact):
                    infected_this_round.add(contact)
            if self.symptomatic_quarantine:
                if person.is_symptomatic(self.current_time):
                    person.quarantines()

        for contact in infected_this_round:
            self.infected.add(contact)
            self.number_infected += 1
            contact.becomes_infected(self.current_time)

            self.susceptible.remove(contact)
            self.number_suspectible -= 1

        for contact in recovers_this_round:
            contact.recovers()
            self.infected.remove(contact)
            self.number_infected -= 1
            self.recovered.add(contact)
            self.number_recovered += 1

        self.current_time += 1
        number_of_new_cases = len(infected_this_round)
        self.number_of_new_cases.append(number_of_new_cases)

    def transmission(self, A, B):

        if A.is_quarantined or B.is_quarantined:
            return False
        else:
            if A.is_contagious(self.current_time) and B.is_susceptible():
                return random.uniform(0, 1) <= self.p
            else:
                return False

    def simulation(self, num_rounds=0):
        if num_rounds:
            for _ in range(num_rounds):
                self.round()
        else:
            while self.infected:
                self.round()


def growth_rate(number_of_new_cases, recovery_time=14):
    length = min(recovery_time, len(number_of_new_cases) - 1)
    total = 0
    for i in range(1, length):
        prev, curr = number_of_new_cases[i - 1], number_of_new_cases[i]
        if prev != 0:
            total += curr / prev
    return total / length


def infection_rate(
    target_growth_rate,
    threshold,
    contact_distribution,
    n=10 ** 3,
    number_of_rounds=None,
    recovery_time=14,
    input_file=None,
):
    actual_growth_rate = 0
    lower, upper = 0, 1
    if input_file is None:
        input_file = "test.txt"
        G = SIR_Graph(n=n, p=1, contact_distribution=contact_distribution)
        G.write_to_file(input_file)
    output_file = f"./output_files/growth_data.csv"
    with open(output_file, "a", buffering=1) as data_file:
        while (
            abs(actual_growth_rate - target_growth_rate) > threshold
            and upper - lower > threshold
        ):
            # print(lower, upper, actual_growth_rate)
            p = (lower + upper) / 2
            H = SIR_Graph(
                file_name=input_file,
                p=p,
                contact_distribution=contact_distribution,
                recovery_time=recovery_time,
            )
            H.simulation(number_of_rounds)
            data_file.write(
                f"{n},{p},{','.join([str(x) for x in H.number_of_new_cases])}\n"
            )
            actual_growth_rate = growth_rate(H.number_of_new_cases)
            if actual_growth_rate > target_growth_rate:
                upper = p
            else:
                lower = p
        return p


def main():
    if len(sys.argv) == 1:
        n = 10 ** 3
    else:
        n = int(sys.argv[1])
    target_growth_rate = 1.1
    p = 0
    threshold = 0.001
    G = SIR_Graph(n=n, p=1, contact_distribution=world_pdf)
    G.write_to_file("graph_1.txt")
    for _ in range(1):
        p += infection_rate(
            target_growth_rate,
            input_file="graph_1.txt",
            contact_distribution=world_pdf,
            threshold=threshold,
        )
    p = p / 1
    print(f"Average infection rate: {p:0.05f}")


if __name__ == "__main__":
    main()
