import json
import pickle

import csv
import os
import threading
import sys
import socket
import subprocess

from datetime import datetime, date
from time import sleep
from datetime import datetime

sys.path.append("/home/haise/Downloads/RPI-ADXL345")
import adxl345

from ina219 import INA219
from ina219 import DeviceRangeError
IP_GS = '127.0.0.1'

#obtener directorio
path_now = os.path.realpath(os.path.dirname(__file__))

#CREACIÓN DE ARCHIVO DE REGISTRO

tm_dic_BASE = { #Keys para generar archivo de registro
							"time": datetime.now(), #tiempo de toma de datos
							"last_com":None, #ultimo comando recibido
							"last_com_date": None, #Fecha ultimo comando recibido
							"v5":0, # linea de 5 volts
							"i5":0, #corriente en 5 volts
							"p5":0, #potencia en 5 volts
							"v3":0, #linea de 3.3 volts
							"i3":0, #corriente en 3.3 volts
							"p3":0, #potencia en 3.3V
							"bat":0,# voltaje de batería
							"sun":0, # voltaje de LDR
							"acce_1_x":0,
							"acce_1_y":0,
							"acce_1_z":0,
							"acce_2_x":0,
							"acce_2_y":0,
							"acce_2_z":0,
							"gyro_X":0,
							"gyro_Y":0,
							"gyro_Z":0,
							}
now = datetime.now()
current_time = now.strftime("%d_M%m_%Y-%H_m%M") #obtener fecha y hora
#crear nombre de archivo para registros
TM_file_new = path_now + f'/TM{current_time}.csv'

with open(TM_file_new, 'w', newline='') as f: # crea archivo
    writer = csv.writer(f)
    writer.writerow(tm_dic_BASE.keys())

def register_file_update(tm_dic): #actualiza el archivo
	with open(TM_file_new, 'a', newline='') as f2:
		writer2 = csv.writer(f2)
		writer2.writerow(tm_dic.values())    
#############################################	

class TELEMETRY():
	def __init__(self):
		self.TM_recorded = None

TM_RCRD = TELEMETRY()

class HAISE_state():
	def __init__(self,end_check_com,last_com, take_pic,linked):
		self.endCheck= end_check_com
		self.last_com = last_com
		self.v5line = 0
		self.i5line = 0
		self.p5line = 0
		self.v3line = 0
		self.i3line = 0
		self.p3line = 0
		self.batline = 0
		self.sunline = 0
		self.acce1x = 0
		self.acce1y = 0
		self.acce1z = 0
		self.acce2x = 0
		self.acce2y = 0
		self.acce2z = 0
		self.gyro_X = 0
		self.gyro_Y = 0
		self.gyro_Z = 0


		self.TAKE_PIC = take_pic
		self.LINKED = linked
		self.ALIVE_FLAG=True
		self.ALIVE_SAT = True
		self.SEND_TM = False

HS = HAISE_state("init",{
							"command":"init",
							"rec_date":"now"
							},
							take_pic=False,
							linked = False
							)
							
def clear():
		#os.system("clear")
		#print("\n\n\n")
		pass

def com_ss():
	global HS
	#socket telecomandos
	while True and HS.ALIVE_FLAG:
		try:
			s = socket.socket(socket.AF_INET,
					socket.SOCK_STREAM)
			bb = True
			attemps = 0
			while bb and attemps < 20:
				try:
					s.connect((IP_GS, 4000))
					HS.LINKED=True
					receive = s.recv(1024)
					print(receive.decode())
					print("Conexión establecida \n")
					sleep(1)					
					bb = False
				except:
					attemps +=1
					receive = False
					# print(f"Attempting connection ... {attemps}")
					pass
			com_t = 0
			while receive and com_t!="end" and not bb:
					clear()
					receive = s.recv(1024)
					time = str(datetime.now())[0:-4]
					com_t = receive.decode() # Recibir telecomando				
					HS.endCheck = com_t
					if com_t != "end":
							com_dic= {
									"command":com_t,
									"rec_date":time
									}
							com_json = json.dumps(com_dic,indent = 1)
							with open("coms.json","w") as updating:
									updating.write(com_json)														
							HS.last_com=com_dic
							print(HS.last_com)
							if com_t =="TAKE_PIC":
								HS.TAKE_PIC=True
							elif com_t == "KILL_OS":
								HS.ALIVE_FLAG = False
								print("KILL")
								break
							elif com_t == "KILL_SAT":
								HS.ALIVE_FLAG = False
								HS.ALIVE_SAT = False
								break
							elif com_t == "GET_TM":
								HS.SEND_TM = True					
					sleep(0.08)					
			s.close()
			HS.LINKED= False
			sleep(1)			
		except Exception as e:
			print(e)
			pass
	
def telemetry_update():
	global TM_RCRD
	while True and HS.ALIVE_FLAG:
		tm_dic = {
								"time": datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")[0:-3], #tiempo de toma de datos now.strftime("%d_M%m_%Y-%H_m%M")
								"last_com":HS.last_com["command"], #ultimo comando recibido
								"last_com_date": HS.last_com["rec_date"],
								"v5":HS.v5line, # linea de 5 volts
								"i5":HS.i5line, #corriente 5V
								"p5":HS.p5line, #potencia en 5V
								"v3":HS.v3line, #linea de 3.3 volts
								"i3":HS.i3line, #corriente 3.3V
								"p3":HS.p3line, #potencia en 3.3V
								"bat":HS.batline,# voltaje de batería
								"sun":HS.sunline, # voltaje de LDR
								# aceleraciones y velocidades angular de acce1=adxl345, acce2= mpu6050
								"acce_1_x":HS.acce1x, 
								"acce_1_y":HS.acce1y,
								"acce_1_z":HS.acce1z,
								"acce_2_x":HS.acce2x,
								"acce_2_y":HS.acce2y,
								"acce_2_z":HS.acce2z,
								"gyro_X":HS.gyro_X,
								"gyro_Y":HS.gyro_Y,
								"gyro_Z":HS.gyro_Z
								}
		TM_RCRD.TM_recorded = tm_dic
		register_file_update(tm_dic)
		sleep(0.5)

def TM_channel():
	global HS
	while True and HS.ALIVE_FLAG:
		try:
			cc = True
			attemps = 0
			if HS.LINKED:
				#socket telemetría	
				s2 = socket.socket(socket.AF_INET,
				  	socket.SOCK_STREAM)
				while cc and attemps < 20:
					try:
						s2.connect((IP_GS, 4500))
						cc = False
					except:
						attemps +=1
						pass	
				while HS.endCheck!="end" and not cc and HS.ALIVE_FLAG:
					tm_data = TM_RCRD.TM_recorded
					
					coded_tm = pickle.dumps(tm_data)		
					s2.send(coded_tm) #Enviar telemetría
					sleep(0.5)
				s2.close()
			sleep(1)
		except Exception as e:
			print(e)
			pass
		
def measure_ADXL345():

	accelerometer = adxl345.ADXL345(i2c_port=1, address=0x53)
	accelerometer.load_calib_value()
	accelerometer.set_data_rate(data_rate=adxl345.DataRate.R_100)
	accelerometer.set_range(g_range=adxl345.Range.G_16, full_res=True)
	accelerometer.measure_start()

	
	while True and HS.ALIVE_FLAG:
			x, y, z = accelerometer.get_3_axis_adjusted()
			HS.acce1x = x
			HS.acce1y = y
			HS.acce1z = z
			HS.pitch_adxl = accelerometer.get_pitch()
			sleep(0.2)
	pass
			
def measure_MPU6050():

	pass

def measure_Power():
	# identificadores
	# ad5v = 0x45
	# adbat = 0x40
	# ad_3v = 0x44
	# ad_sol = 0x41
	def read(ina):
		b_v = ina.voltage()
		try:
				b_c = ina.current()
				b_p = ina.power()
		except DeviceRangeError as e:
				print(e)
		return b_v, b_c, b_p
	SHUNT_OHMS = 0.1
	max_AMP = 1.0
	ad5v = 0x45
	adbat = 0x40
	ad_3v = 0x44
	ad_sol = 0x41
	ina_5v = INA219(SHUNT_OHMS,max_AMP,address=ad5v)
	ina_5v.configure(ina_5v.RANGE_16V)
	ina_bat = INA219(SHUNT_OHMS,max_AMP,address=adbat)
	ina_bat.configure(ina_bat.RANGE_16V)
	ina_3v = INA219(SHUNT_OHMS,max_AMP,address=ad_3v)
	ina_3v.configure(ina_3v.RANGE_16V)
	ina_sol = INA219(SHUNT_OHMS,max_AMP,address=ad_sol)
	ina_sol.configure(ina_bat.RANGE_16V)
	while True and HS.ALIVE_FLAG:
		V5_line = read(ina_5v)
		bat_line =read(ina_bat)
		v3_line =read(ina_3v)
		sol_line = read(ina_sol)
		HS.v5line = V5_line[0]
		HS.i5line = V5_line[1]
		HS.p5line = V5_line[2]
		HS.batline = bat_line[0]
		bat_i = bat_line[1]
		bat_p = bat_line[2]
		HS.v3line = v3_line[0]
		HS.i3line = v3_line[1]
		HS.p3line = v3_line[2]
		HS.sunline = sol_line[0]
		sol_i = sol_line[1]
		sol_p = sol_line[2]
		sleep(0.2)
	pass

#socket imagenes
def take_pic():
	global HS
	while True and HS.ALIVE_FLAG:
		try: 
			while HS.endCheck!="end" and HS.LINKED and HS.ALIVE_FLAG:
				if HS.TAKE_PIC:
					subprocess.run(["raspistill","-o","\home\haise\image.jpg","-w","1920","-h","1080"])					
					s3 = socket.socket(socket.AF_INET,
							socket.SOCK_STREAM)	
					dd = True
					attemps = 0
					while dd and attemps < 20:
						try:
							s3.connect((IP_GS, 3000))
							
							dd = False
						except:
							attemps +=1
							print(attemps)
							pass		
					#im = open("c:/Users/Robocop/Desktop/HAISE/imagen.jpg","rb")
					im = open("\home\haise\image.jpg","rb")
					jj = 0
					for i in im:
						s3.send(i)						
					HS.TAKE_PIC=False
					print("image sent")
					sleep(0.5)
					s3.close()				
			sleep(1)	
		except Exception as e:
			print(e)
			pass					

# Enviar toda la telemetría registrada desde que se encendió el satelite.	
def send_all_TM():
	while True and HS.ALIVE_FLAG:
		try:
			cc = True
			attemps = 0
			if HS.SEND_TM and HS.LINKED:
				#socket telemetría	
				s_tm = socket.socket(socket.AF_INET,
				  	socket.SOCK_STREAM)
				while cc and attemps < 20:
					try:
						s_tm.connect((IP_GS,7000))
						cc=False							
					except Exception as e:
						attemps +=1
						print (e)						
						if attemps>20:
							HS.SEND_TM = False
				with open(TM_file_new, "r") as f:
					reader = csv.reader(f)
					for i, line in enumerate(reader):					
						s_tm.send(pickle.dumps(line))			
				s_tm.close()
				HS.SEND_TM = False
								
		except Exception as e:
			print(e)
			pass
		sleep(1)	

if __name__== "__main__":
	#Threads para multiprocesos
	t_coms = threading.Thread(target=com_ss)
	t_coms.daemon = True

	t_tm_up = threading.Thread(target=telemetry_update)
	t_tm_up.daemon = True

	t_tm_send = threading.Thread(target=TM_channel)
	t_tm_send.daemon = True

	t_camera = threading.Thread(target=take_pic)
	t_camera.daemon = True

	t_all_TM = threading.Thread(target=send_all_TM)
	t_all_TM.daemon = True

	t_power = threading.Thread(target=measure_Power)
	t_power.daemon = True
	t_ADXL = threading.Thread(target=measure_ADXL345)
	t_ADXL.daemon = True

	t_coms.start()
	sleep(0.2)
	t_tm_up.start()
	t_tm_send.start()
	t_camera.start()
	t_all_TM.start()
	t_power.start()
	t_ADXL.start()
	
	t_coms.join()
	sleep(0.2)
	t_tm_up.join()
	t_tm_send.join()
	t_camera.join()
	t_all_TM.join()
	t_power.join()
	t_ADXL.join()
	
	if not HS.ALIVE_SAT:
		print("Power Off")
		os.system("sudo shutdown now")
	sys.exit()


