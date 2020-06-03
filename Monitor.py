#relevant imports
from numpy import arange
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib as mpl
import threading
import matplotlib.pyplot as plt
import math
from subprocess import call
from os import _exit

# set parameter for graph colours
COLOR = 'white'
mpl.rcParams['text.color'] = COLOR
mpl.rcParams['axes.labelcolor'] = COLOR
mpl.rcParams['xtick.color'] = COLOR
mpl.rcParams['ytick.color'] = COLOR
plt.style.use('dark_background')

# main UI class
class GUI:
    # initialise the class
    def __init__(self, master):
        global t1, t2 # allow access to extra threads outside object
        #set window properties and bind F11 and escape keys to fullscreen toggle functions
        self.master = master
        master.title("System Monitor")
        self.master.iconbitmap('icon3.ico')
        self.master.attributes("-toolwindow", 1)
        self.master.bind("<F11>", self.fullscreen_toggle)
        self.master.bind("<Escape>", self.fullscreen_cancel)
        #set data lists and error handling flags
        self.cpu_data = []
        self.ram_data = []
        self.gpu_data = []
        self.cpu_temp = []
        self.gpu_temp = []
        self.total = []
        self.x_counter = []
        self.data_queue = []
        self.fail_count = 0
        self.new_instance = True
        
        #initialise figure for plotting
        self.figure = Figure(facecolor='black')
        
        #generate 6 subplots in a 2 row 3 column grid
        #subplot title will display what is being measured and its current value
        #x-ticks are hidden as they are arbitrary, ylims are set to show 0-100% or 0-100 degrees for each graph
        self.cpu_graph = self.figure.add_subplot(231)
        self.cpu_graph.set(ylabel='% Used')
        self.cpu_graph.xaxis.set_ticklabels([])
        self.cpu_graph.set_ylim(0,101)
        self.cpu_graph.grid(True, alpha=0.5)
        self.cpu_graph.plot(self.x_counter,self.cpu_data,color='c')
        
        self.gpu_graph = self.figure.add_subplot(232)
        self.gpu_graph.set(ylabel='% Used')
        self.gpu_graph.xaxis.set_ticklabels([])
        self.gpu_graph.set_ylim(0,101)
        self.gpu_graph.grid(True, alpha=0.5)
        self.gpu_graph.plot(self.x_counter,self.gpu_data,color='m')
        
        self.ram_graph = self.figure.add_subplot(233)
        self.ram_graph.set(ylabel='% Used')
        self.ram_graph.xaxis.set_ticklabels([])
        self.ram_graph.set_ylim(0,101)
        self.ram_graph.grid(True, alpha=0.5)
        self.ram_graph.plot(self.x_counter,self.ram_data,color='yellow')
        
        self.cpu_temp_graph = self.figure.add_subplot(234)
        self.cpu_temp_graph.set(ylabel='°C')
        self.cpu_temp_graph.xaxis.set_ticklabels([])
        self.cpu_temp_graph.set_ylim(0,101)
        self.cpu_temp_graph.grid(True, alpha=0.5)
        self.cpu_temp_graph.plot(self.x_counter,self.cpu_temp,color='orangered')
        
        self.gpu_temp_graph = self.figure.add_subplot(235)
        self.gpu_temp_graph.set(ylabel='°C')
        self.gpu_temp_graph.xaxis.set_ticklabels([])
        self.gpu_temp_graph.set_ylim(0,101)
        self.gpu_temp_graph.grid(True, alpha=0.5)
        self.gpu_temp_graph.plot(self.x_counter,self.gpu_temp,color='lime')
        
        #special figure,  bar plot on polar axes for total system usage, average of cpu, ram and gpu usage
        #set up to fill clockwise for higher usage and scale from 0-100 percent corresponding to 0-180 degrees
        self.system_plot = self.figure.add_subplot(236, projection='polar')
        self.system_plot.set_thetamin(0)
        self.system_plot.set_thetamax(180)
        self.system_plot.set_theta_zero_location('W')
        self.system_plot.set_theta_direction(-1)
        self.system_plot.set_thetagrids([0, 60, 120, 180], labels=[0, 25, 75, 100])
        self.system_plot.set_rgrids([0.4, 0.2, 0, -0.2, -0.4], labels=[])
        self.system_plot.barh(0, math.radians(0), color='hotpink')
        
        #configure the canvas aas the only widget and plot the figure on it
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)  # A tk.DrawingArea.
        self.canvas.get_tk_widget().configure(background='black',  highlightcolor='black', highlightbackground='black')
        self.figure.tight_layout()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.canvas.draw()
        self.master.update()
        
        #start a daemon thread for fetching system info and another daemon thread for cheking the data queue
        t1 = threading.Thread(target=self.get_info, daemon=True)
        t1.start()
        t2 = threading.Thread(target=self.CheckQueue, daemon=True)
        t2.start()
        
    # function to activate fullscreen mode hiding the window manager for borderless fullscreen
    def fullscreen_toggle(self, event="none"):
        self.master.focus_set()
        self.master.overrideredirect(True)
        self.master.attributes("-fullscreen", True)
        self.master.wm_attributes("-topmost", 1)

    #function to switch out of fullscreen and bring window manager back
    def fullscreen_cancel(self, event="none"):
        self.master.overrideredirect(False)
        self.master.attributes("-fullscreen", False)
        self.master.wm_attributes("-topmost", 0)
    
    #function ran by thread to repeatedly poll the data queue and if new data is available call function to update graphs 
    def CheckQueue(self):
        #this block fails if there is on data to process, in this case it iwll skip to the end and wait 1 second before recalling
        try:
            #raw corresponds to an array of data, one piece for each graph
            #raw data is sent to the corresponding graphs data list
            raw = self.data_queue[0]
            self.data_queue.pop(0)
            self.cpu_data.append(raw[0])
            self.ram_data.append(raw[1])
            self.gpu_data.append(raw[2])
            self.cpu_temp.append(raw[3])
            self.gpu_temp.append(raw[4])
            self.total.append(raw[5])
            
            #to keep memory consumption down no mroe than ten pieces of data are stored per grpah at any time
            #if more than 10 exist the first piece is removed
            if(len(self.cpu_data)>10):
                self.cpu_data.pop(0)
                self.ram_data.pop(0)
                self.gpu_data.pop(0)
                self.cpu_temp.pop(0)
                self.gpu_temp.pop(0)
                self.total.pop(0)
                self.x_counter.pop(0)
            
            #x_counter is an arbitrary x value that increases by one on each iteratorion to show graph moving in real-time
            if(len(self.x_counter)>0):
                self.x_counter.append(self.x_counter[len(self.x_counter)-1] + 1)
            elif(len(self.x_counter)==0):
                self.x_counter.append(1)
            
            #call function to update the graphs with the new data
            self.update_graph()
        
        except:
            pass
        
        #wait one second and then call function to check the queue again
        self.master.after(1000, self.CheckQueue)
        
    #function to update the graphs in the window     
    def update_graph(self):
        #same process repeated for each graph
        #clear graph axes and replot as in __init__ with the new data
        self.cpu_graph.cla()
        self.cpu_graph.title.set_text("CPU Usage\n%3.1f%%" % self.cpu_data[-1])
        self.cpu_graph.set(ylabel='% Used')
        self.cpu_graph.set_xticks(arange(self.x_counter[0],self.x_counter[len(self.x_counter)-1],1))
        self.cpu_graph.xaxis.set_ticklabels([])
        self.cpu_graph.set_ylim(0,101)
        self.cpu_graph.set_xlim(self.x_counter[0],self.x_counter[len(self.x_counter)-1])
        self.cpu_graph.grid(True, alpha=0.5)
        self.cpu_graph.plot(self.x_counter,self.cpu_data,color='c')
        
        self.gpu_graph.cla()
        self.gpu_graph.title.set_text("GPU Usage\n%3.1f%%" % self.gpu_data[-1])
        self.gpu_graph.set(ylabel='% Used')
        self.gpu_graph.set_xticks(arange(self.x_counter[0],self.x_counter[len(self.x_counter)-1],1))
        self.gpu_graph.xaxis.set_ticklabels([])
        self.gpu_graph.set_ylim(0,101)
        self.gpu_graph.set_xlim(self.x_counter[0],self.x_counter[len(self.x_counter)-1])
        self.gpu_graph.grid(True, alpha=0.5)
        self.gpu_graph.plot(self.x_counter,self.gpu_data,color='m')
        
        self.ram_graph.cla()
        self.ram_graph.title.set_text("RAM Usage\n%3.1f%%" % self.ram_data[-1])
        self.ram_graph.set(ylabel='% Used')
        self.ram_graph.set_xticks(arange(self.x_counter[0],self.x_counter[len(self.x_counter)-1],1))
        self.ram_graph.xaxis.set_ticklabels([])
        self.ram_graph.set_ylim(0,101)
        self.ram_graph.set_xlim(self.x_counter[0],self.x_counter[len(self.x_counter)-1])
        self.ram_graph.grid(True, alpha=0.5)
        self.ram_graph.plot(self.x_counter,self.ram_data,color='yellow')
        
        self.cpu_temp_graph.cla()
        self.cpu_temp_graph.title.set_text("CPU Temperature\n%3.1f°C" % self.cpu_temp[-1])
        self.cpu_temp_graph.set(ylabel='°C')
        self.cpu_temp_graph.set_xticks(arange(self.x_counter[0],self.x_counter[len(self.x_counter)-1],1))
        self.cpu_temp_graph.xaxis.set_ticklabels([])
        self.cpu_temp_graph.set_ylim(0,101)
        self.cpu_temp_graph.set_xlim(self.x_counter[0],self.x_counter[len(self.x_counter)-1])
        self.cpu_temp_graph.grid(True, alpha=0.5)
        self.cpu_temp_graph.plot(self.x_counter,self.cpu_temp,color='orangered')
        
        self.gpu_temp_graph.cla()
        self.gpu_temp_graph.title.set_text("GPU Temperature\n%3.1f°C" % self.gpu_temp[-1])
        self.gpu_temp_graph.set(ylabel='°C')
        self.gpu_temp_graph.set_xticks(arange(self.x_counter[0],self.x_counter[len(self.x_counter)-1],1))
        self.gpu_temp_graph.xaxis.set_ticklabels([])
        self.gpu_temp_graph.set_ylim(0,101)
        self.gpu_temp_graph.set_xlim(self.x_counter[0],self.x_counter[len(self.x_counter)-1])
        self.gpu_temp_graph.grid(True, alpha=0.5)
        self.gpu_temp_graph.plot(self.x_counter,self.gpu_temp,color='lime')
        
        self.system_plot.cla()
        self.system_plot.title.set_text("Total Usage\n%3.1f%%" % self.total[-1])
        new_data = self.total[-1]*1.8 #percentage is converted in to degrees, 1% = 1 degree because 180 degrees is 100% on these axes
        self.system_plot.set_thetamin(0)
        self.system_plot.set_thetamax(180)
        self.system_plot.set_theta_zero_location('W')
        self.system_plot.set_theta_direction(-1)
        self.system_plot.set_thetagrids([0, 45, 90, 135, 180], labels=[0, 25, 50, 75, 100])
        self.system_plot.set_rgrids([0.4, 0.2, 0, -0.2, -0.4], labels=[])
        self.system_plot.barh(0, math.radians(new_data), color='hotpink')
        
        #ensure no figure overlap and black colour scheme does not change, redraw canvas
        self.figure.tight_layout()
        self.canvas.get_tk_widget().configure(background='black',  highlightcolor='black', highlightbackground='black')
        self.canvas.draw()

    #function that runs in a thread to continuously fetch new data to display
    def get_info(self):
        #this block corresponds to the fail-safe to try and keep the programrunning
        #if it has run 50 iterations (duration = 0.5 seconds) without finding new data it will read file with failure count
        #it will increase the failure count by one, this number is checked by the relaunching software
        #after updating the fail count the function will close the software
        #will also run a .vbs script to launch it without any pop-up or focus stealing, handling is in place to ensure this does not continuously happen
        if(self.fail_count>50):
            file = open('FailCheck.txt','r')
            data = int(file.read())
            file.close()
            data+=1
            file = open('FailCheck.txt','w')
            file.write(str(data))
            file.close()
            call('wscript.exe Invisible.vbs')
            _exit(1)
        else:
            pass
        
        #try and open the data log file and take the most recent data, if fails increase fail count and recall
        try:
            with open('HardwareMonitoring.txt','r') as f:
                lines = f.read().splitlines()
                last_line = lines[-1]
        except:
            self.fail_count+=1
            self.master.after(100, self.get_info)
        
        #try and open the data log and empty it to prevent excessive file sizes for data that will not be processed, if fails increase fail count and recall
        try:
            with open('HardwareMonitoring.txt','w+') as f:
                f.truncate()
        except:
            self.fail_count+=1
            self.master.after(100, self.get_info)
        
        #remove whitespace and turn data columns in to list, if you want to save different data or configure afterburner logging differently you may need to change this step
        #float each piece of data and store it to variable, append processed data to data queue
        #if process fails increase fail count and recall
        try:
            data = last_line.replace(' ','').split(',')[2:7]
            iterator=0
            for x in data:
                y = float(x)
                data[iterator] = y
                iterator+=1
            
            gpu_temp, gpu, cpu_temp, cpu, ram = data
            ram = (ram/16384)*100 #IMPORTANT- CONVER RAM TO PERCENTAGE USED, DIVIDE BY THE TOTAL RAM IN SYSTEM, IN MY CASE 16GB
            total = (cpu + ram + gpu) / 3 #get total usage stat as average of three usage stats
            #append the data queue witha  list of data in order specified by the check queue function
            self.data_queue.append([cpu, ram, gpu, cpu_temp, gpu_temp, total])
            #reset fail count for successful data fetch
            self.fail_count=0
    
        except:
            self.fail_count+=1
            self.master.after(100, self.get_info)
        
        #if data was stored in queue and this is the first run of a relaunch mark the times failed as 0
        #this will reset the error checking because the application is behaving normally again
        if(self.data_queue!=[] and self.new_instance==True):
            file = open('FailCheck.txt','w')
            file.write('0')
            file.close()
            self.new_instance = False
        
        #recall the function after one second
        self.master.after(1000, self.get_info)


if(__name__ == '__main__'): 
    # Initiialise a black tkinter window
    root = Tk()
    root.configure(background='black')
    # Set window properties to match display being used, in my case a 720x457 monitor in fullscreen
    w = 720
    h = 457
    root.overrideredirect(True)
    root.geometry('%dx%d+%d+%d' % (w,h,-2648,77)) #last two ordinate are monitor coordinates in my setup (3 monitor)
    # 0,0 corresponds to top left of primary display, these numbers were found fullscreening application with window.winfo_x(), window.winfo_y()
    root.update()
    root.focus_force()
    # initialise GUI class
    my_gui = GUI(root)
    root.mainloop()
    # if main thread closes window terminate the remaining threads
    t1.join()
    t2.join()









