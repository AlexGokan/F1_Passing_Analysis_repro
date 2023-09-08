import numpy as np
import matplotlib.pyplot as plt

import requests
import json
import pickle
import cv2
import os
import pathlib
import time
import scipy.stats as st
import pathlib

import seaborn as sns
sns.set_theme()

#configuration variables concerning data loading
I_already_have_the_data = True
I_promise_not_to_hammer_the_ergast_api = False

#make the output directory
out_dir = 'f1_passing_stats_demo/'
out_path = pathlib.Path(out_dir)
if not out_path.is_dir():
	os.mkdir(out_path)

def get_table_for_year_and_num(circuit_id,year):
	#returns the qualfying and finishing positions for a specified race, with extra detail stripped out
	
	season = str(year)
	if year not in year_and_round_of_circuit[circuit_id]:
		return 'qualy,podium',[],[]
	race_num = str(year_and_round_of_circuit[circuit_id][year])
	
	
	request_str = 'http://ergast.com/api/f1/{}/{}/results.json'.format(season,race_num)

	response = requests.get(request_str)
	rj = response.json()

	results = rj["MRData"]['RaceTable']['Races'][0]['Results']

	starts = []
	ends = []
	
	for place in range(len(results)):
		result = results[place]
		finishing_place = place+1
		starting_place = int(result['grid'])
		
		#detect a DNS
		DNS = False
		pit_start = False
		if result['laps'] == '0':
			DNS = True
			
		#detect a pit-lane start
		if result['grid'] == '0' and not DNS:
			pit_start = True
		
		if not DNS:
			if pit_start:
				starting_place = 20
			starts.append(starting_place)
			ends.append(finishing_place)

	return 'qualy,podium',starts,ends



years_to_consider = list(range(1950,2023+1))


#get the round numbers for each circuit and year
if I_already_have_the_data:
	with open('all_circuits.json','r') as F:
		data = F.readlines()[0]
		data = json.loads(data)
	data2 = {}
	for circuit in data:#convert all the years from string to int since json can't do integer keys
		d = data[circuit]
		#print(d)
		data2[circuit] = {}
		for year in d:
			iyear = int(year)
			data2[circuit][iyear] = data[circuit][year]
	year_and_round_of_circuit = data2
else:
	if not I_promise_not_to_hammer_the_ergast_api:
		print('ERROR: please modify line 17 to promise not to violate rate limits and retry')
		quit()
	year_and_round_of_circuit = {}
	for year in years_to_consider:
		round_num = 1
		valid_circ = True
		while valid_circ:
			request_str = 'http://ergast.com/api/f1/{}/{}/circuits.json'.format(str(year),str(round_num))
			response = requests.get(request_str)
			time.sleep(20)#rate-limit, do not modify
			rj = response.json()
			
			clist = rj['MRData']['CircuitTable']['Circuits']
			print(clist)
			if len(clist) == 0:
				valid_circ = False
			else:
				cid = rj['MRData']['CircuitTable']['Circuits'][0]['circuitId']
				print(cid,year)
				
				if cid not in year_and_round_of_circuit:
					year_and_round_of_circuit[cid] = {year:round_num}
				else:
					year_and_round_of_circuit[cid][year] = round_num
					
			round_num += 1
			


			
	#with open('all_circuits.obj','wb') as F:
	#	pickle.dump(year_and_round_of_circuit,F)
		
	with open('all_circuits.json','w') as F:
		F.write(json.dumps(year_and_round_of_circuit,indent=4))
		
			

#remove races that haven't happened yet (adjust for your use) (this code written before zandvoort 2023)
year_and_round_of_circuit['monza'].pop(2023)
year_and_round_of_circuit['zandvoort'].pop(2023)
year_and_round_of_circuit['marina_bay'].pop(2023)
year_and_round_of_circuit['suzuka'].pop(2023)
year_and_round_of_circuit['losail'].pop(2023)
year_and_round_of_circuit['americas'].pop(2023)
year_and_round_of_circuit['rodriguez'].pop(2023)
year_and_round_of_circuit['interlagos'].pop(2023)
year_and_round_of_circuit['vegas'].pop(2023)
year_and_round_of_circuit['yas_marina'].pop(2023)

circuits = list(year_and_round_of_circuit.keys())

if I_already_have_the_data:
	with open('f1_results.json','r') as F:
		data = F.readlines()[0]
		data = json.loads(data)
	
	results = {}
	for circuit in data:
		results[circuit] = {}
		for year in data[circuit]:
			iyear = int(year)
			qual,race = data[circuit][year]
			results[circuit][iyear] = (qual,race)	
else:
	if not I_promise_not_to_hammer_the_ergast_api:
		print('ERROR: please modify line 17 to promise not to violate rate limits and retry')
		quit()
	results = {}
	circuits = list(year_and_round_of_circuit.keys())

	for circuit in circuits:
		race_instances = year_and_round_of_circuit[circuit]
		
		for year in race_instances:
			print(circuit,year)
			
			round_num = race_instances[year]
			
			label,starts,ends = get_table_for_year_and_num(circuit,year)
			time.sleep(20)#rate-limit, do not modify unless you want to potentially be cut off by ergast
			if circuit not in results:
				results[circuit] = {year:(starts,ends)}
			else:
				results[circuit][year] = (starts,ends)

	with open('f1_results.json','w') as F:
		#pickle.dump(results,F)
		F.write(json.dumps(results,indent=4))
		


print(results['silverstone'])

#data acquisition finished here

#generate year-by-year statistics

r2_by_race = {}
for circuit in circuits:
	race_instances = year_and_round_of_circuit[circuit]
	for year in race_instances:

		quals,finish = results[circuit][year]
		r = np.corrcoef(quals,finish)[0,1]
		r2 = np.sign(r) * r * r
		
		if circuit not in r2_by_race:
			r2_by_race[circuit] = {year:r2}
		else:
			r2_by_race[circuit][year] = r2
		
"""
result_corrs = {}#"r",sqrt(r^2),correlation coefficient, etc
for circuit in circuits:
	race_instances = year_and_round_of_circuit[circuit]
	
	for year in race_instances:
		
		starts,ends = results[circuit][year]
		start_end_corr = np.corrcoef(starts,ends)[0,1]
		
		
		if circuit not in result_corrs:
			result_corrs[circuit] = {year:start_end_corr}
		else:
			result_corrs[circuit][year] = start_end_corr

"""

r2_by_year = {}
mean_r2_by_year = {}
median_r2_by_year = {}
for circuit in circuits:
	race_instances = year_and_round_of_circuit[circuit]
	for year in race_instances:
		if not year in r2_by_year:
			r2_by_year[year] = []
		
		this_race_r2 = r2_by_race[circuit][year]
		
		r2_by_year[year].append(this_race_r2)

"""
corr_by_year = {}
for circuit in circuits:
	race_instances = year_and_round_of_circuit[circuit]
	for year in race_instances:
		if not year in corr_by_year:
			corr_by_year[year] = []
		
		this_race_corr = result_corrs[circuit][year]
		
		corr_by_year[year].append(this_race_corr)
"""


		
mean_r2_by_year = {}
median_r2_by_year = {}
r2_lower_ci = {}
r2_upper_ci = {}

for idx,year in enumerate(years_to_consider):
	
	r2 = r2_by_year[year]
	
	
	mean_r2_by_year[year] = np.mean(r2)
	median_r2_by_year[year] = np.median(r2)

	
	
	ci_low,ci_high = st.t.interval(0.95,len(r2)-1,loc=np.mean(r2),scale=st.sem(r2))#95-percent confidence intervals
	
	r2_upper_ci[year] = ci_high
	r2_lower_ci[year] = ci_low


#####################################################################################
#generate plot points

race_r2_x = []
race_r2_y = []
lci_y = []
hci_y = []
ci_x = []
mean_r2_y = []
median_r2_y = []
median_r2_x = []
for idx,year in enumerate(years_to_consider):
	r2 = r2_by_year[year]
	
	for elem in r2:
		race_r2_x.append(year)
		race_r2_y.append(elem)
	
	ci_x.append(year)
	lci_y.append(r2_lower_ci[year])
	hci_y.append(r2_upper_ci[year])
	
	mean_r2_y.append(mean_r2_by_year[year])
	median_r2_y.append(median_r2_by_year[year])
	median_r2_x.append(year)
	
	


from matplotlib.pyplot import figure


fig = plt.figure(figsize=(20,10),dpi=250)

LW = 3
plt.plot(median_r2_x,mean_r2_y,label='mean',linewidth=LW)
plt.plot(median_r2_x,median_r2_y,label='median',linewidth=LW)

plt.plot(ci_x,lci_y,linewidth=LW,color=(0,1,0,0.25))
plt.plot(ci_x,hci_y,linewidth=LW,color=(0,1,0,0.25))

plt.scatter(race_r2_x,race_r2_y,color=(0,0,1,0.25))

plt.ylim(-1,1)
plt.axhline(y=0,c='black')

#eras of F1 as defined by https://en.wikipedia.org/wiki/History_of_Formula_One
plt.axvline(x=1957.5,c='black')
plt.axvline(x=1961.5,c='black')
plt.axvline(x=1967.5,c='black')
plt.axvline(x=1976.5,c='black')
plt.axvline(x=1982.5,c='black')
plt.axvline(x=1988.5,c='black')
plt.axvline(x=1993.5,c='black')
plt.axvline(x=1994.5,c='black')
plt.axvline(x=1999.5,c='black')
plt.axvline(x=2005.5,c='black')
plt.axvline(x=2008.5,c='black')
plt.axvline(x=2013.5,c='black')
plt.axvline(x=2021.5,c='black')

plt.ylim([-0.2,0.6])

plt.title('start grid pass-stat by year')
plt.gca().invert_yaxis()

plt.legend()

plt.savefig(out_path / pathlib.Path('r2_avg_by_year.png'))
#plt.show()



def create_r2_plot(circuit):#year-by-year pass stat for a given circuit
	xdata = r2_by_race[circuit].keys()
	ydata = r2_by_race[circuit].values()
	ydata = np.array(list(ydata))
	
	fig = plt.figure(figsize=(10,5),dpi=400)
	
	plt.plot(xdata,ydata)
	plt.scatter(xdata,ydata,s=15)
	plt.xlim(1949,2024)
	plt.axhline(y=0,c=(1,0,0,0.5))
	plt.title('pass-stat at {}'.format(circuit.title()))
	plt.ylim([-0.55,1])
	plt.gca().invert_yaxis()
	filename = out_path / pathlib.Path('{}_r2.png'.format(circuit))
	plt.savefig(filename)


circuits_to_plot = ['albert_park','americas','bahrain','brands_hatch','catalunya','estoril','galvez','hockenheimring','hungaroring','imola','indianapolis','interlagos','jacarepagua','kyalami','magny_cours','marina_bay','monaco','monza','nurburgring','red_bull_ring','reims','ricard','rodriguez','sepang','shanghai','silverstone','spa','suzuka','villeneuve','watkins_glen','yas_marina','zandvoort','zolder']

for circuit in circuits_to_plot:
	create_r2_plot(circuit)


#circuits which have been raced >6 times after a certain year
def common_circuits_after_year(first_year):
	recent_circuits = []
	sample_size = {}
	for circuit in year_and_round_of_circuit:
		years = year_and_round_of_circuit[circuit].keys()
		years = np.array(list(years))
		
		recently = years>=first_year
		if sum(recently) > 6:
			recent_circuits.append(circuit)
			sample_size[circuit] = sum(recently)
			
	recent_corrs = {}
	recent_r2 = {}
	
			
	for circuit in recent_circuits:
		circuit_recent_r2s = []
		for year in range(first_year,2023+1):
			if year in r2_by_race[circuit]:
				circuit_recent_r2s.append(r2_by_race[circuit][year])
				
		recent_r2[circuit] = np.mean(circuit_recent_r2s)
		
	return recent_r2,sample_size

recent_r2,sample_size = common_circuits_after_year(2006)
recent_r2,sample_size = common_circuits_after_year(2014)


def write_recent_results(year,recent_r2,sample_size):#generate a csv output
	rec_s = dict(sorted(recent_r2.items(),key=lambda item: item[1]))
	with open(out_path / pathlib.Path('recent_results_{}.csv'.format(year)),'w') as F:
		F.write('circuit name,pass stat,sample size\n')
		for circuit in rec_s:
			c_name = circuit
			c_name = c_name.replace('_',' ')
			c_name = c_name.title()
			output_string = '{},{},{}\n'.format(c_name,rec_s[circuit],sample_size[circuit])
			F.write(output_string)

year = 2014;write_recent_results(year,*common_circuits_after_year(year))
year = 2006;write_recent_results(year,*common_circuits_after_year(year))


def hmnorm(x):#normalization function for showing heatmaps
    x = np.copy(x)
    x -= x.min()
    x /= sum(x)
    return x

def create_heatmap(circuit):
	grid = np.zeros((20,20))
	for year in results[circuit]:
		qual,race = results[circuit][year]
		for i in range(len(qual)):
			qual_pos = qual[i] - 1
			race_pos = race[i] - 1
			if qual_pos <= 19 and race_pos <= 19:#remove drivers outside the top 20 for the years that had >20 drivers to simplify analysis
				grid[qual_pos,race_pos] += 1	
	
	
	fig = plt.figure(figsize=(5,5),dpi=250)
	plt.imshow(hmnorm(grid),vmin=0,vmax=1.0)
	plt.gca().invert_yaxis()
	plt.yticks([0,5,10,15])
	plt.xticks([0,5,10,15])
	plt.xlabel('starting position')
	plt.ylabel('finishing position')
	plt.title('Heatmap for {}'.format(circuit.title()))
	plt.colorbar()

	plt.savefig(out_path / pathlib.Path('{}_heatmap.png'.format(circuit)))
	
for circuit in circuits_to_plot:
	create_heatmap(circuit)
