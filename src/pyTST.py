# -*- coding: utf-8 -*-
"""
Created on August 10 2019
@author: Rong Huangfu

Notes:
The Shoulder Tool 0.1.0 initial draft
0.1.1 updated metric option and links to LiFFT and DUET
0.1.2 changed force direction option; updated model relationship based on 681 uts

TODO: 
0812: Metrix unit option; change strength value based on direction and left/right side of shoulder;
automate dania data processing; show different health outcome ; show plots;

"""
import math

class TST(object):

    def __init__(self, unit, direction, lever_arm, load, rep):
        import colorsys
        self.unit = unit.lower()
        self.direction = direction
        self.rep = float(rep)
        #print(self.unit)
        if self.unit == "imperial":
            self.lever_arm = float(lever_arm)
            self.load = float(load)
        elif self.unit == "metric":
            self.lever_arm = float(lever_arm) / 2.54  # cm to inch
            self.load = float(load) / 4.45 # N to lb

        def hsv2rgb(h, s, v):
            return tuple(int(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

        color_HSV = []

        for n in range(110, 10, -1):  # reversed order of range
            H, S, V = n / 360.0, 1, 1
            R, G, B = hsv2rgb(H, S, V)
            packed = str('#%02x%02x%02x' % (R, G, B))
            color_HSV.append(str(packed))

        color_HSV_new = []

        for i in range(len(color_HSV)):
            if i < 5:
                color_HSV_new.append(color_HSV[i])
            elif i % 2 != 0 and i < 52 and i > 5:  # - 26
                color_HSV_new.append(color_HSV[i])
            elif i >= 52 and i < 62:  # + 5
                color_HSV_new.append(color_HSV[i])
                if i % 2 == 0:
                    color_HSV_new.append(color_HSV[i])
            elif i >= 62 and i % 3 == 0:  # - 26
                color_HSV_new.append(color_HSV[i])


        color_HSV_new = color_HSV_new + [color_HSV[-1]] * 49

        self.color_list = color_HSV_new
        self.out_range_colorlist = ['#ff2e00']

        #print(len(self.color_list))

    def riskFromDamage(self, damage_input): # return prob(first time office visit)
        cd = math.log(damage_input, 10)
        #y = 0.67 + 0.867 * cd # v0.1.1
        y = 0.864 + 0.928 * cd # v0.1.2
        p = math.exp(y) / (1 + math.exp(y))
        return p

    def colorFromDamageRisk(self, damage_input):
        d = damage_input
        if d < 0.00002:
            return self.color_list[0]
        elif d > 136:
            return self.color_list[-1]
        else:
            risk_value = self.riskFromDamage(damage_input)
            risk_index = int(risk_value * 100)
            return self.color_list[risk_index]

    # calculate moment based on direction of force
    def moment_cal(self, direction, lever_arm, load):
        # "0": lift up, "1": push/pull down, "2": push forward, "3": pull backward
        # inch, lbs
        if lever_arm >= 1.715 and lever_arm < 27:
            arm_moment = (-8.27 + 4.8223 * lever_arm)/12.0 # ft lbs
        elif lever_arm >= 27:
            arm_moment = 121.9 / 12.0
        else: 
            arm_moment = 0

        load_moment = load * lever_arm / 12.0 # ft lbs

        if direction == "0":
            #print("0\n") 
            return load_moment + arm_moment
        elif direction == "1":
            #print("1\n")
            return load_moment
        elif direction == "2":
            #print("2\n")
            return abs(load_moment - arm_moment)
       

    def percycle_damage_cal(self, moment, uts=681):
        return 1.0/(10**((101.25-100*(moment*12/uts))/14.83))

    def calculate(self):

        moment = self.moment_cal(self.direction, self.lever_arm, self.load)
        d_percycle = self.percycle_damage_cal(moment) # unit: ft.lb

        if self.unit == "metric":
            moment = (moment / 0.73756) * 9.81 # ft.lb to N.m
        else:
            pass
        moment = round(moment, 1)

        task_damge = round((d_percycle * self.rep), 5)
        color = self.colorFromDamageRisk(task_damge)

        return moment, task_damge, color


               
                    
                

          
       
   
