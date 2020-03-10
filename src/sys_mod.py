import numpy as np 
import time 
import os 
import logging
import subprocess 
import argparse
import sys 
import const_mod 
import random 

def is_int(a): 

	try: 

		int(a) 	

	except ValueError: 

		return False 

	return True 	

def is_string(a):  

	try: 

		str(a) 

	except ValueError: 

		return False 

	return True 

def is_float(a): 

	try: 

		float(a) 

	except ValueError: 

		return False 

	return True 

def get_lines(filename):

	with open(filename,"r") as content:

		for i,l in enumerate(content):

			pass

	return i+1

#-----------------------------------------------------------------------------
#---------------------------- Command Line -----------------------------------
#-----------------------------------------------------------------------------

class ReadCommandLine():

	@classmethod
	def __init__(cls): 

		return None  

	@classmethod
	def Finish(cls,jobID=None,total_cores=None,input_file=None,mode=None):  

		if ( jobID is not None ):

			cls.JOBID = jobID 

		if ( total_cores is not None ): 

			cls.TOTAL_CORES = total_cores
		
		if ( input_file is not None ): 

			cls.INPUT = input_file	
			
		if ( mode is None ):  

			cls.MODE = "run"

		else: 

			cls.MODE = "debug"

		if ( total_cores is None and jobID is None and input_file is None and mode is None ):
		
			cls.Take_Command_Line_Args() 

			cls.Parse_Input_Argument()
	
		cls.logger = cls.Set_Run_Mode(cls.JOBID +".log",cls.MODE)  
			
		return cls.logger,cls.TOTAL_CORES,cls.INPUT, cls.JOBID

	@classmethod 
	def Take_Command_Line_Args(cls): 
		
		parser = argparse.ArgumentParser()

		parser.add_argument("-c", "--cores", type=int, required=True)

		parser.add_argument("-i", "--input", type=str, required=True)

		parser.add_argument("-j", "--job", type=str, required=True) 
		
		#parser.add_argument("-n", "--node", type=str, required=True)

		parser.add_argument("-m", "--mode", type=str, required=False)

		args = parser.parse_args()

		cls.argument = dict( args.__dict__.iteritems() )  

		return None  

	@classmethod
	def Parse_Input_Argument(cls):  

		cls.JOBID = cls.argument["job"]  
	
		cls.TOTAL_CORES = cls.argument["cores"] 

		"""
		if ( cls.argument["mode"] == None):

			cls.MODE = "run" 

		else: 

			cls.MODE = "debug" 

		"""
		cls.INPUT = cls.argument["input"] 

		return None  

	@classmethod
	def Select_Run_Mode(cls,arg): 

		mode = { 
		
		"debug": logging.DEBUG, 
		"run": logging.INFO

		}  
		
		mode.get(arg,"invalid") 

		if ( mode[arg] == "invalid"):  

			print "Invalid Run mode: Choose debug or run"

			sys.exit()  

		return mode[arg] 

	@classmethod
	def Select_Formatter(cls,arg): 

		mode = { 
		
		"debug": "%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
		"run": "%(message)s" 
		}  

		mode.get(arg,"invalid") 
		
		if ( mode[arg] == "invalid"): 

			print "Invalid Run mode: Choose debug or run"

			sys.exit()  
		
		return mode[arg] 
		
	@classmethod
	def Set_Run_Mode(cls,logname,mode): 

		logger = logging.getLogger() 

		logger.setLevel(cls.Select_Run_Mode(mode)) 

		fh = logging.FileHandler(logname,mode="w")

		formatter = logging.Formatter(cls.Select_Formatter(mode)) 

		fh.setFormatter(formatter) 

		logger.addHandler(fh) 

		return logger

	def choose_cores_for_LAMMPS(self,total_atoms,max_cores): 
		
		"""
		Determine how many cores needed to run LAMMPS. 

		--Argument: 

		total_atoms: system size  

		max_cores: max number of cores requested

		--Returns: 

		num_cores: number of cores assigned to LAMMPS 

		"""

		if ( max_cores <= 8 ): 

			return max_cores 	

		elif ( 10 <= max_cores ): 

			if ( total_atoms <= 500 ):  

				return min(max_cores,4) 

			elif ( 500 < total_atoms <= 1000) : 

				return min(max_cores,6)    	

			elif ( 1000 < total_atoms <= 2000 ) : 

				return min(max_cores,10) 	
		
		elif ( 2000 < total_atoms <= 3000 ) : 
		
			return min(max_cores,14)   

		elif ( 3000 < total_atoms <= 4000 ) :  

			return min(max_cores,18)  

		elif ( 4000 < total_atoms <= 5000 ) : 

			return min(max_cores,22)  

#-----------------------------------------------------------------------------
#---------------------------- Input Parameters -------------------------------
#-----------------------------------------------------------------------------

class ParseInputFile():  

	# each line of data must matched with the order of following inputkeyword

	inputkeyword = ["units",
					"matchingtype",
					"command",
					"restart",
					"guess_parameter",
					"fit_and_fix",
					"constraints",
					"termination_criterion",
					"options",
					"argument"] 

	def __init__(self,filename): 

		# get the file name

		self.filename = filename 

		# number of lines to pointer for certain keywords 	
		
		self.pointer = 0 
		
		try: 

			with open(self.filename,"r") as inputfile: 

				pass

		# except FileNotFoundError #in Python 3

		except IOError:  

			print "Input file for optimizations is not found"

			# terminate the program 

			sys.exit() 

		self.Read_Content()
	
		self.Get_Parameters() 	

		return None 

	# Read all contents from input file into a variable "self.parameters"  

	def Read_Content(self):

		with open(self.filename,"r") as inputfile: 
		
			self.parameters = []  

			for line in inputfile:

				contents = line.split()    
			
				# skip the empty lines 

				if ( contents == [] ): 

					continue 

				# skip the comment due to "#" or "&" 

				elif ( "#" in contents[0] or "&" in contents[0]): 

					continue

				else:

					self.parameters.append(contents) 

		return None 
		
	# Error Checking for each type of input  

	def CheckJobname(self): 

		if ( len(self.parameters[self.pointer]) > 1): 

			print "Only 1 job name should be provided; more than 1 is given here "

			sys.exit()  			
		
		return None 	

	def CheckRestart(self): 

		if ( len(self.parameters[self.pointer]) > 1): 

			print "Only 1 restart frequency value should be provided; more than 1 is given here "

			sys.exit()  			
		
		return None 
	
	def CheckGuess(self): 

		if (self.guess_parameter.size != self.fit_and_fix.size ): 

			print "The number of parameters provided is not equal to fitted parameters (=1) + unfitted parameters (=0) " 

			sys.exit()  

	def CheckFitFix(self): 

		if ( np.any(self.fit_and_fix > 1 ) or np.any(self.fit_and_fix < 0 )) : 

			print "Fit Fix ERROR: only 1 or 0 is allowed "

	def CheckMode(self):

		if ( self.mode != "Restart" and  self.mode != "Perturb"):  

			print "MODE ERROR! : Check the spelling or type: must choose either 'Restart' or 'Perturb' to initialize Nelder-Mead Simplex  "

			sys.exit() 

	def CheckPerturb(self): 

		fit_size = ( self.fit_and_fix==1 ).sum()  

		if ( self.mode == "Perturb" and fit_size != self.perturb.size ):   	

			print  "Simplex Size ERROR: The number of fitted parameters (=1) should be equal to number of perturbed parameters " 

			sys.exit() 

		if ( self.mode =="Restart" and fit_size != self.purturb.size -1 ): 

			print "Simplex Size ERROR: The number of fitted parameters + 1  (=1) should be equal to number of vertices " 

			sys.exit() 

	def CheckRestartpara(self): 

		vertices_shape = self.vertices.shape  
	
		if ( vertices_shape[0] <= vertices_shape[1] ): 

			print "The number of vertices is larger than the number of objective functions"	

			sys.exit() 

		if ( vertices_shape[0] != self.obj.size ): 

			print "Restart Simplex ERROR!: number of vertices are not equal to number of objectives" 

			sys.exit() 

	def CheckConstraints(self):  

		if ( len(self.constraints )%3 != 0 or len(self.constraints ) < 3 ): 
		
			print "Constraints ERROR: index, lowerbound, upperbound should be provided together" 

			sys.exit() 

		if ( np.amax(self.constraints_index) > self.guess_parameter.size -1 ): 

			print "Constraints ERROR: The constraints index provided is out of bound" 

			sys.exit() 


		for cindex in self.constraints_index:

			if ( cindex  in self.unfit):
				
				print "Constrains ERROR: Constraint index has to be fitted variable (=1). Unfitted variable (=0) can not be constrained "

				sys.exit()
				 
	def units(self):  

		units = self.parameters[self.pointer]

		self.UNITS = const_mod.Units(str(units[0])) 		
	
		self.units_name = str(units[0]) 
		
		self.pointer = self.pointer + 1 

		return None 
	
	def This_line_is_matchingtype(self,a):  

		results = [ is_string(a[0]), is_string(a[1]), is_float(a[2]) , is_int(a[3]), is_int(a[4]) ] 

		num_True = results.count(True) 

		return num_True 

	def matchingtype(self): 	

		self.matching = [] 
		
		counter = 0 

		while True:

			parse_matching_para = self.This_line_is_matchingtype(self.parameters[self.pointer]) 

			if ( parse_matching_para == 5):   

				matching_type = " ".join(self.parameters[self.pointer]) 
	
				self.matching.append(matching_type)  

				self.pointer = self.pointer + 1 

				counter = counter + 1  

			elif ( 3 <= parse_matching_para < 5 ): 
	
				print "Format ERROR: Make Sure your input follows: matchingtype (str), ID (int) , weight (float), cores for MD (int), cores for analysis (int) "

				sys.exit() 
		
			else: 	

				break 

		return None 

	def command(self):

		run = " " 
	
		run_command = run.join(self.parameters[self.pointer])

		self.run_command = run_command  

		self.pointer = self.pointer + 1 
		
		return None 

	# get the restart frequency: 

	def restart(self): 

		try: 
	
			self.restart = int(self.parameters[self.pointer][0]) 
			
		except ( ValueError, TypeError): 

			print "Input file: Restart frquency must be an integer value "

			sys.exit() 

		self.CheckRestart()

		self.pointer = self.pointer + 1 

		return None 

		# get the guess parameters:  

	def guess_parameter(self):  

		try: 

			self.ptype = self.parameters[self.pointer][0]

			self.guess_parameter = np.array(self.parameters[self.pointer][1:]).astype(np.float64) 

		except ( ValueError, TypeError): 

			print "Input file: Guess Parameters ERROR!: can't read guess data ! Make sure they are all floats  "

			sys.exit() 

		if ( is_float(self.ptype) or is_int(self.ptype) ): 
			
			print "The first guess parameters must be potential type (string) " 
			
			sys.exit()    

		self.pointer = self.pointer + 1 

		return None 

	
	# get the fitted or unfitted parameters: 

	def fit_and_fix(self):  

		try: 

			self.fit_and_fix = np.array(self.parameters[self.pointer]).astype(np.int) 

		except ( TypeError,ValueError): 

			print "Input file: fit and fix ERROR!: can't read fit and fix data ! Make sure they are all integers "
	
			sys.exit()  

		self.fit = np.array([ i for i,x in enumerate(self.fit_and_fix) if x == 1  ],dtype=np.int) 

		self.unfit = np.array([ i for i,x in enumerate(self.fit_and_fix) if x ==0 ],dtype=np.int) 

		self.guess = self.guess_parameter[self.fit] 
	
		self.CheckGuess() 

		self.CheckFitFix() 

		self.pointer = self.pointer + 1 

		return None 
	
	# get the constraints 

	def constraints(self):  

		self.constraints = np.array(self.parameters[self.pointer])

		num_constraints = len(self.constraints)/3 

		if ( self.constraints[0] == "None" or self.constraints[0] == "none"): 

			self.constraints_index = np.array([])  
	
			self.constraints_fit_index = np.array([]) 

			self.constraints_bound = np.array([]) 

		else: 

			try: 

				self.constraints_index = np.array([self.constraints[idx*3]  for idx in xrange(num_constraints)]).astype(np.int)-1 

				self.constraints_fit_index = np.zeros(self.constraints_index.size).astype(np.int)  

				for nindex in xrange(self.constraints_index.size): 

					# shift the index due to fix variable.  

					num_shift = sum( i < self.constraints_index[nindex] for i in self.unfit) 

					self.constraints_fit_index[nindex] = self.constraints_index[nindex] - num_shift 

				self.constraints_bound = np.array([ [ self.constraints[3*indx+1], self.constraints[3*indx+2]] for indx in xrange(num_constraints)]) 	

			except ( ValueError, TypeError) : 

				print "Input file: Constraints ERROR!: can't read constraints parameter ! Make sure their types are correct " 

				sys.exit() 

			self.CheckConstraints() 

			self.constraints_bound.astype(np.float32) 

		self.pointer = self.pointer + 1 

		return None

	# get the termination criterino: maximum number of iterations,parameters tol, objective tol: 

	def termination_criterion(self): 

		try: 
    
			self.max_iteration = int(self.parameters[self.pointer][0]) 
	
			self.para_tol = float(self.parameters[self.pointer][1]) 

			self.obj_tol = float(self.parameters[self.pointer][2]) 
     
		except ( ValueError, TypeError): 

			print "Input file Errors: Maximum number of iteration must be integer; parameters and objective tol be float"

			sys.exit() 

		self.pointer = self.pointer + 1  

		return None 	

	# get the options of either Perturb or Restart  

	def options(self): 
	
		if ( "options" in self.inputkeyword ):

			#indx = self.inputkeyword.index("options") 
		
			try: 
			
				self.mode = self.parameters[self.pointer][0]  
				
			except ( ValueError, TypeError): 

				print "Input file: Keyword option ERROR!: Specify Restart or Perturb"

				sys.exit() 
					
			self.CheckMode() 

			self.pointer = self.pointer + 1

		return None 	

	# get the argument of either perturb or restart

	def Check_Perturb_Argument(self,argument): 

		if ( argument[1] != "+" and argument[1] != "-" and argument[1]  != "random" ): 

			print " For Perturb options: first argument must be '+','-', or 'random' "

			sys.exit() 

		if ( not is_float(argument[2]) and argument[2]  != "random" ):
	
			print "For Perturb options: second argument must be float type between '0-1', or 'random' " 	

			sys.exit() 

		return None 
		
	def argument(self):  

		#indx = self.inputkeyword.index("argument") 

		if ( self.mode =="Perturb"):  

			# get Perturb argument in that lines 
			arglist = self.parameters[self.pointer-1:self.pointer]

			# if Perturb + argument are equal 3; read it  	
			self.perturb_argument = arglist[0]

			if ( len(arglist[0]) == 3 ): 
					
				# check perturb argument 	
					
				self.Check_Perturb_Argument(arglist[0])	
			
				n_fit_parameter = np.count_nonzero(self.fit_and_fix)   

				self.perturb = self.decide_perturbation_stepsize(n_fit_parameter) 		

			# Perturb + argument can not be greater than 3  	

			elif ( len(arglist[0]) > 3 ): 

				print "Too many arguments for Perturb: at most 2 are needed ( e.g. Perturb + 0.5 ) " 
	
				sys.exit() 

			# if only Perturb exists, then manual input of perturb parameters should be given 

			elif ( len(arglist[0]) ==1 ): 

				try: 

					self.perturb = np.array(self.parameters[self.pointer:self.pointer+1][0] ).astype(np.float64)  

					self.pointer = self.pointer + 1 

				except ( ValueError, TypeError): 

					print "Input file: Perturb parameters ERROR! They should be all floats"
					
					sys.exit() 

				self.CheckPerturb() 

			else: 

				print "Perturb needs either no argument or two arguments ( e.g. Perturb random random ) "
	
				sys.exit() 

		elif ( self.mode =="Restart"): 

			try: 

				self.obj = np.array(self.parameters[self.pointer:self.pointer+1][0] ).astype(np.float64)
				
				num_v = self.obj.size   

				self.pointer = self.pointer + 1 
				
				self.vertices = np.array(self.parameters[self.pointer:self.pointer+num_v+1] ).astype(np.float64) 
					
				self.pointer = self.pointer + num_v 	
					
			except ( ValueError, TypeError) : 

				print "Input file: ERROR in Reading restart parameters ! "  

				sys.exit() 	

			self.CheckRestartpara() 

		return None 

	def generate_perturb_sign(self,n_vertices,perturb_arg): 

		if ( perturb_arg == "random"): 

			return  np.array([ int(random.choice(["1","-1"])) for i in xrange(n_vertices) ]) 	

		elif (perturb_arg == "+" ): 
			
			return np.array([ 1 for i in xrange(n_vertices) ]) 	
				
		elif ( perturb_arg == "-") : 

			return np.array([ -1 for i in xrange(n_vertices) ]) 	

	def generate_perturb_magnitude(self,n_vertices,perturb_arg):

		if ( perturb_arg == "random" ):

			return np.array([ random.choice([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]) for i in xrange(n_vertices) ]) 
			
		else:  
			
			return np.array([ float(perturb_arg) for i in xrange(n_vertices) ]) 	

	def decide_perturbation_stepsize(self,n_vertices):

		arg  = self.perturb_argument 

		if ( len(arg) == 3 ):   

			sign_option = arg[1] 

			val_options = arg[2]

			sign = self.generate_perturb_sign(n_vertices,sign_option) 

			val = self.generate_perturb_magnitude(n_vertices,val_options)

			return sign*val 	

	def Get_Parameters(self):

		for para in self.inputkeyword: 
	
			each_para = getattr(self,para) 

			each_para() 

		return None 

#-----------------------------------------------------------------------------
#--------------------------------- Folders Setup -----------------------------
#-----------------------------------------------------------------------------

class Setup(): 

	ref_folder = "../ReferenceData"

	prep_folder = "../prepsystem"

	predict_folder = "Predicted"

	def __init__(self,jobid,matching_in,overwrite=None): 

		if ( overwrite == True ):
		
			self.overwrite = True	

		else: 

			self.overwrite = False

		self.home = os.getcwd() 

		self.matching_type = np.unique([ everytype.split()[0]\
							 for everytype in matching_in ])	

		self.subfolders_per_type = self.Get_subfolders_from_type(self.matching_type,matching_in )		

		self.jobid = jobid 

		self.Check_Folders(self.ref_folder,self.matching_type,self.subfolders_per_type)

		self.Check_Folders(self.prep_folder,self.matching_type,self.subfolders_per_type)

		self.Mkdir() 

		return None 

	def Get_subfolders_from_type(self,matching_type,matching_in ): 

		subfolders_per_type = {} 
	
		for typename in matching_type: 	

			type_sub = [] 
	
			for everytype in matching_in: 

				args = everytype.split() 

				if ( args[0] == typename): 

					type_sub.append(args[1]) 
				
			subfolders_per_type[typename] = type_sub	
		
		return subfolders_per_type 

	def Check_Folders(self,address,matching_type,subfolders_per_type):

		folder_exists = os.path.isdir(address) 

		if ( not folder_exists ): 

			print "ERROR: folder " + address + " does not exist" 

			sys.exit()

		if ( len(os.listdir(address+"/" )) == 0 )  : 

			print "ERROR: No folders inside " + address   
		
			sys.exit() 

		for match in matching_type: 

			for subfolder in subfolders_per_type[match]: 

				match_folder = address + "/" + match + "/" + subfolder 
				
				if ( not os.path.isdir( match_folder)): 

					print "ERROR: folders: " + match_folder 
					print "Check the following: \n"
					print "1. Does the type %s exist ?"%match 
					print "2. Is this folder name consistent with the matching type name used in input file e.g. isobar, force etc ?"
					print "3. Does the subfolder (e.g. 1 2 ...) index of this type exist ?"
		
					sys.exit()	

				if ( len(os.listdir(match_folder+"/")) ==0):
			
					print "ERROR: No files inside: ",match_folder 		
		
					sys.exit() 
		
		return None

	def Mkdir(self): 	
		
		job_folder = self.jobid + "/"

		working_folders = job_folder + self.predict_folder 
	
		if ( os.path.isdir(job_folder) and self.overwrite==False): 

			print "%s exists! set 'overwrite=True' upon instantiation "%job_folder	

			sys.exit()

		elif ( os.path.isdir(job_folder) and self.overwrite==True ):
		
			print "overwrite the existing folder: %s ! "%job_folder	

			os.system("rm -r %s"%job_folder) 

			time.sleep(1) 	
			
		os.mkdir(job_folder)

		os.mkdir(working_folders)

		os.mkdir(job_folder + "Restart") 

		os.mkdir(job_folder + "Output")

		self.predict_folder_list= [ ] 

		self.ref_folder_list = [] 

		for everytype in self.matching_type: 
	
			self.job_folders = working_folders + "/" + everytype + "/" 
	
			os.mkdir(self.job_folders)	

			self.predict_folder_list.append(self.job_folders)  
		
			self.ref_folder_list.append(self.ref_folder + "/" + everytype ) 
	
		return None 

	def Go_to_Subfolders(self,sub_folders): 

		folders = next(os.walk('.'))[1] 

		if ( folders ): 

			for folder in folders: 

				os.chdir(folder) 

				self.Go_to_Subfolders(sub_folders) 

				os.chdir("../")

		else: 

			sub_folders.append(os.getcwd()) 

		return sub_folders
	
	def Get_Path(self,wk_folder): 

		os.chdir(wk_folder) 

		sub_folders = []  

		sub_folders = self.Go_to_Subfolders(sub_folders) 

		num_folders = len(sub_folders)  	

		os.chdir(self.home) 

		return num_folders,sub_folders 

	def Get_Folders_Path(self,main_folders,sub_folder_type):  

		job_address = { } 

		for indx,folder in enumerate(main_folders): 

			sub_index_type = {} 
							
			for sub_indx in sub_folder_type[self.matching_type[indx]]: 	

				num_jobs,sub_folders = self.Get_Path(folder + "/" + sub_indx) 

				sub_folders.sort() 

				sub_index_type[sub_indx] = sub_folders  
	
				job_address[self.matching_type[indx]] = sub_index_type 

		return job_address

	def Transfer_Prepsystem_To_Predict_Folder(self): 

		for indx,matching_type in enumerate(self.matching_type): 

			for sub_indx in self.subfolders_per_type[matching_type]:  

				subprocess.call("cp"+ " -r " 
								+ self.prep_folder + "/" + "%s/%s" %( matching_type,sub_indx )
								+  " " + self.predict_folder_list[indx], shell=True ) 

		return None 

	def Finish(self): 

		self.Transfer_Prepsystem_To_Predict_Folder()

		ref_job_address = self.Get_Folders_Path( self.ref_folder_list,self.subfolders_per_type ) 	

		predict_job_address = self.Get_Folders_Path( self.predict_folder_list,self.subfolders_per_type)

		return self.home,ref_job_address,predict_job_address

#-----------------------------------------------------------------------------
#---------------------------- Output -----------------------------------------
#-----------------------------------------------------------------------------

class Output(): 

	def __init__(self,input_para,jobID): 

		self.jobID = jobID 

		self.restart_address = str(jobID) + "/" + "Restart" + "/" 

		self.output_address  = str(self.jobID) + "/" + "Output" + "/" 

		self.input_para = input_para

		self.restart_log_file = self.restart_address + "log.restart"
	
		self.current_restart_file = self.restart_address + "current.restart"	

		self.vertices_file = self.output_address + "best_worst.vertices"

		self.matching_func_file = self.output_address + "costfunction.txt"
	
		self.best_para_file = self.output_address + "best_parameters.txt" 
		
		open(self.restart_log_file,"w").close()
	
		open(self.current_restart_file,"w").close()
		
		open(self.vertices_file,"w").close() 

		open(self.matching_func_file,"w").close() 
		
		return None 

	def Update_Properties(self,address,list_of_file): 

		for filename in list_of_file: 

			write_file = address + "/"+ filename

			subprocess.call("cp" + " -r " + " " + write_file + " " + self.output_address,shell=True ) 	

		return None 

	def Write_Cost_Func(self,itera,costfunction): 

		with open(self.matching_func_file,"a") as out: 

			np.savetxt(out,zip(itera,costfunction)) 	

		return None 	

	def Write_Best_Worst_Vertices(self,itera,best_vertices,worst_vertices):
	
		with open(self.vertices_file,"a") as out:

			out.write(str(itera) + "  " +  str(best_vertices) + "  " + str(worst_vertices) + "\n")
						
		return None 

	def Write_Best_Parameters(self,current_best_parameter): 

		with open(self.best_para_file,"w") as out: 

			out.write(" ".join(str(para) for para in current_best_parameter)) 

		return None 

	def Write_Restart(self,itera,best_parameter,vertice_para,vertice_cost):

		if ( itera % self.input_para.restart == 0 ):	

			best_and_fix = np.zeros(self.input_para.fit_and_fix.size)	

			best_and_fix[self.input_para.fit_and_fix==1] = best_parameter	

			best_and_fix[self.input_para.fit_and_fix==0] = self.input_para.guess_parameter[self.input_para.fit_and_fix == 0] 	

			self.best_and_fix = best_and_fix	

			with open(self.restart_log_file,"a") as f:	
			
				self.RestartContent(f,itera,vertice_para,vertice_cost)	

			with open(self.current_restart_file,"w") as f:	

				self.RestartContent(f,itera,vertice_para,vertice_cost) 	

		return None 

	def RestartContent(self,f,itera,vertice_para,vertice_cost):  

		contents_header = "# Iteration: " + str(itera) + "\n\n"

		bestparameter_header = "# Guess initial Parameters: \n\n"

		f.write(contents_header) 

		f.write("\n")

		f.write("# LAMMPS units\n\n") 

		f.write(self.input_para.units_name) 

		f.write("\n \n") 

		f.write("# Matching type ( type, subindex, weight,cores for lammps, cores for analysis \n\n")

		for match in self.input_para.matching: 
	
			f.write(match + "\n") 	

		f.write("\n")
	
		f.write("# Command \n\n")

		f.write(self.input_para.run_command + "\n\n") 

		f.write("# Restart frequency \n\n")

		f.write(str(self.input_para.restart)) 

		#f.write(self.best_and_fix) 

		f.write("\n\n")

		f.write(bestparameter_header) 		

		guess_parameter = " ".join( str(ele) for ele in self.input_para.guess_parameter )  

		f.write(self.input_para.ptype +  " "  + guess_parameter)

		#np.savetxt(f,self.best_and_fix,newline=" ",fmt="%.10f") 

		f.write("\n \n") 

		f.write("# fit (1) and fix (0) parameters: ") 

		f.write("\n \n") 

		np.savetxt(f,self.input_para.fit_and_fix,newline=" ",fmt="%d") 
		
		f.write("\n \n") 

		f.write("# constraints ( index lower-bound upper-bound ... ): ")

		f.write("\n \n") 

		np.savetxt(f,self.input_para.constraints,newline=" ", fmt="%s") 		

		f.write("\n\n") 

		f.write("#set termination criterion: max number of iteration, tolerance for parameters,tolerance for objective \n\n") 

		termination = np.array([self.input_para.max_iteration,self.input_para.obj_tol,self.input_para.para_tol]) 	

		np.savetxt(f,termination,newline=" ", fmt="%s") 

		f.write("\n\n") 
		f.write("# create (Perturb) or use existing vertices (Restart): ") 
		f.write("\n \n") 

		if ( self.input_para.mode == "Perturb"): 
				
			f.write( "#"+ " ".join( str(ele) for ele in self.input_para.perturb) )  
			
		f.write("\n \n" )
		f.write("Restart") 
		f.write("\n \n" ) 

		np.savetxt(f,vertice_cost,newline=" ",fmt="%.8e") 
		f.write("\n \n") 
	
		np.savetxt(f,vertice_para,fmt="%.10f") 

		f.write("\n \n") 
		
		return None 

