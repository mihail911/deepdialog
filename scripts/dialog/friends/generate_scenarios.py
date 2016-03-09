__author__ = 'anushabala'
import re

date_range_pattern = r'([0-9]{4})-([0-9]{}4)'
import numpy as np
from argparse import ArgumentParser
import json
from collections import defaultdict
import os


class Friend(object):
    def __init__(self, name, major, school, school_start, school_end, company=None, company_start=None,
                 company_end=None):
        self.name = name
        self.school = {'major': major,
                       'name': school,
                       'start': school_start,
                       'end': school_end}
        if company and company_start and company_end:
            self.company = {'name': company,
                            'start': company_start,
                            'end': company_end}
        else:
            self.company = None

    def __info__(self):
        return {
            "name": self.name,
            "school": self.school,
            "company": self.company,
        }

    def same_school(self, other_friend):
        return self.school["name"] == other_friend.school["name"]

    def same_major_and_school(self, other_friend):
        return self.school["major"] == other_friend.school["major"] and self.same_school(other_friend)

    def same_company(self, other_friend):
        if not self.company or not other_friend.company:
            return False
        return self.company["name"] == other_friend.company["name"]

    def school_overlap(self, other_friend):
        if not self.same_school(other_friend):
            return False
        # my_range = xrange(self.school["start"], self.school["end"]+1)
        other_range = xrange(other_friend.school["start"], other_friend.school["end"] + 1)
        if self.school["start"] in other_range or self.school["end"] in other_range:
            return True

    def company_overlap(self, other_friend):
        if not self.company or not other_friend.company:
            return False
        if not self.same_company(other_friend):
            return False
        # my_range = xrange(self.company["start"], self.company["end"]+1)
        other_range = xrange(other_friend.company["start"], other_friend.company["end"] + 1)
        if self.company["start"] in other_range or self.company["end"] in other_range:
            return True


class FriendNetwork(object):
    def __init__(self):
        self.friends = []
        self.relationships = defaultdict(list)

    def __info__(self):
        return [friend.__info__() for friend in self.friends]

    def add_relationship(self, user1, user2):
        self.relationships[user1].append(user2)
        self.relationships[user2].append(user1)

    def add_friend(self, friend):
        self.friends.append(friend)

    def find_potential_friends(self, friend):
        potential_friends = []
        for other_friend in self.friends:
            if other_friend.name != friend.name:
                if (friend.same_major_and_school(other_friend) or friend.same_school(other_friend)) and friend.school_overlap(other_friend):
                    potential_friends.append(other_friend)
                elif friend.same_company(other_friend) and friend.company_overlap(other_friend):
                    potential_friends.append(other_friend)
        return potential_friends

    def find_second_degree_friends(self):
        second_degree = []
        added_friends = []
        for person in self.friends:
            added_friends.append(person)
            my_friends = self.relationships[person]
            for friend in my_friends:
                other_friends = self.relationships[friend]
                connections = [f for f in other_friends if f not in my_friends and f not in added_friends]
                second_degree.extend([(person, connection, friend) for connection in connections])

        return second_degree


class NetworkGenerator(object):
    majors = ['Computer Science', 'Physics', 'Math',
              'Economics', 'Linguistics']

    schools = ['Stanford', 'Columbia',
               'University of Pennsylvania', 'University of California - Berkeley']

    companies = ['Google', 'Facebook', 'Apple', 'Uber', 'Amazon']

    current_year = 2016
    min_year = 2006
    school_duration = xrange(2, 5)
    company_duration = xrange(0, 10)
    same_school = 0.4
    same_major_and_school = 0.5
    same_company = 0.5
    p_threshold = 0.2

    def generate_random_friend(self, name):
        major = np.random.choice(self.majors)
        school = np.random.choice(self.schools)
        school_start = np.random.choice(xrange(self.min_year, self.current_year + 1))
        school_end = min(school_start + np.random.choice(self.school_duration), self.current_year)
        if school_end < self.current_year:
            company = np.random.choice(self.companies)
            company_start = np.random.choice(xrange(school_end, self.current_year))
            company_end = min(company_start + np.random.choice(self.company_duration), self.current_year)
            return Friend(name, major, school, school_start, school_end, company, company_start, company_end)
        return Friend(name, major, school, school_start, school_end)

    def __init__(self, N=50, names_file='data/person_names.txt'):
        self.network_size = N
        self.names = list(set([line.strip() for line in open(names_file, 'r').readlines()]))
        self.network = None

    def create_network(self):
        self.network = FriendNetwork()
        selected_names = np.random.choice(self.names, self.network_size, replace=False)
        for name in selected_names:
            friend = self.generate_random_friend(name)
            self.network.add_friend(friend)
            potential_friends = self.network.find_potential_friends(friend)
            self.create_relationships(friend, potential_friends)

    def create_relationships(self, friend, potential_friends):
        for other_friend in potential_friends:
            p = 0
            if friend.same_major_and_school(other_friend):
                p += np.random.uniform(0, self.same_major_and_school)
                # print "same major and school", p
            elif friend.same_school(other_friend):
                p += np.random.uniform(0, self.same_school)
                # print "same school", p

            if friend.same_company(other_friend):
                p += np.random.uniform(0, self.same_company)
                # print "same company", p

            if p >= self.p_threshold:
                # print "Adding relationship between 2 friends"
                # print friend.__info__()
                # print other_friend.__info__()
                self.network.add_relationship(friend, other_friend)


class ScenarioGenerator(object):
    def __init__(self, network):
        self.network = network
        self.second_degrees = network.find_second_degree_friends()

    def generate_scenario(self, num_friends=50):
        scenario = {}
        connected_users = self.second_degrees[np.random.choice(xrange(0, len(self.second_degrees)))]
        user1 = connected_users[0]
        user2 = connected_users[1]
        connection = connected_users[2]
        user1_friends = [connection]
        user2_friends = [connection]
        scenario["user1"] = {"info": user1.__info__()}
        scenario["user2"] = {"info": user2.__info__()}



        # add all friends of each user except their mutual friends (apart from the one common connection
        user1_friends.extend([f for f in self.network.relationships[user1] if f not in self.network.relationships[user2]])
        user2_friends.extend([f for f in self.network.relationships[user2] if f not in self.network.relationships[user1]])

        # print len(user1_friends), len(user2_friends)
        ctr = 0
        while ctr < len(self.network.friends) and \
                        len(user1_friends) < num_friends:
            friend = self.network.friends[ctr]
            if friend == user1 or friend == user2 or friend == connection:
                ctr += 1
                continue
            if friend not in self.network.relationships[user2] and friend not in self.network.relationships[user1]:
                if friend not in user2_friends and np.random.uniform() <= 0.5:
                    user1_friends.append(friend)
            ctr += 1


        ctr = 0
        while ctr < len(self.network.friends) and \
                        len(user2_friends) < num_friends:
            friend = self.network.friends[ctr]
            if friend == user1 or friend == user2 or friend == connection:
                ctr += 1
                continue
            if friend not in self.network.relationships[user2] and friend not in self.network.relationships[user1]:
                if friend not in user1_friends and np.random.uniform() <= 0.5:
                    user2_friends.append(friend)
            ctr += 1

        # print len(user1_friends), len(user2_friends)
        np.random.shuffle(user1_friends)
        np.random.shuffle(user2_friends)
        scenario["user1"]["friends"] = [f.__info__() for f in user1_friends]
        scenario["user2"]["friends"] = [f.__info__() for f in user2_friends]

        common = [f for f in user1_friends if f in user2_friends]
        assert len(common)==1, "error"
        return scenario


def write_user(info, outfile, fewer_lines=False):
    outfile.write("\tName: %s" % info["name"])
    outfile.write("\n")
    outfile.write("\tSchool: %s" % info["school"]["name"])
    if fewer_lines:
        outfile.write("\t")
    else:
        outfile.write("\n")
    outfile.write("\tMajor: %s" % info["school"]["major"])
    if fewer_lines:
        outfile.write("\t")
    else:
        outfile.write("\n")
    outfile.write("\tSchool dates: %d - %d" % (info["school"]["start"], info["school"]["end"]))
    outfile.write("\n")
    if info["company"]:
        outfile.write("\tCompany: %s" % info["company"]["name"])
        if fewer_lines:
            outfile.write("\t")
        else:
            outfile.write("\n")
        outfile.write("\tCompany dates: %d - %d\n" % (info["company"]["start"], info["company"]["end"]))
    
    
def write_scenario_to_readable_file(scenario, user1_file, user2_file):
    write_user(scenario["user1"]["info"], user1_file)
    user1_file.write("Friends:\n")
    for f in scenario["user1"]["friends"]:
        write_user(f, user1_file, fewer_lines=True)
        user1_file.write("\n")
    write_user(scenario["user2"]["info"], user2_file)
    user2_file.write("Friends:\n")
    for f in scenario["user2"]["friends"]:
        write_user(f, user2_file, fewer_lines=True)
        user2_file.write("\n")


def write_json_to_file(network, outfile):
    json_network = json.dumps(network.__info__())
    outfile.write(json_network+"\n")


def main(args):
    outfile = open(args.output, 'w')

    num_scenarios = args.num_scenarios
    num_networks = args.num_networks
    generator = NetworkGenerator(args.size)
    generator.create_network()
    for i in xrange(0, num_scenarios):
        scen_file_1 = open(os.path.join(args.scenario_dir, 'scenario%d_User1.out' % i,), 'w')
        scen_file_2 = open(os.path.join(args.scenario_dir, 'scenario%d_User2.out' % i,), 'w')
        scenario_gen = ScenarioGenerator(generator.network)
        scenario = scenario_gen.generate_scenario(num_friends=10)
        write_scenario_to_readable_file(scenario, scen_file_1, scen_file_2)
        write_json_to_file(generator.network, outfile)
        scen_file_1.close()
        scen_file_2.close()

    outfile.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--size', type=int, default=50, help='Size of network to generate')
    parser.add_argument('--output', type=str, default='data/scenarios.json', help='File to write networks to.')
    parser.add_argument('--num_scenarios', type=int, default=100, help='Number of scenarios to generate')
    parser.add_argument('--num_networks', type=int, default=1, help='Number of networks to generate')
    parser.add_argument('--scenario_dir', default='data/scenarios', help='File to write scenario to')

    clargs = parser.parse_args()
    main(clargs)