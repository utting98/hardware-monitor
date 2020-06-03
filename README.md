# hardware-monitor
Python project to process and display live graphs of hardware usage information logged by MSI Afterburner

![Example Screen](Example.jpg)

The aim of this project was to produce a series of graphs showing some hardware usage and temperatures on a small monitor to be mounted inside my PC. 

The code is designed around the setup I am using but can be customised for your needs, areas that may need customisation are highlighted within comments in the code.

For my use the code was compiled by auto-py-to-exe and the Restart.bat file launches expecting an executable, if you are not compiling to an executable then this batch file will need to be adjusted accordingly.

This program requires Msi Afterburner to be installed and logging to the same directory as the Monitor.py (or Monitor.exe) script. To use this program out of the box the graphs being logged by Msi should be: GPU temperature, GPU usage, CPU temperature, CPU usage and RAM usage. All other graphs should be switched off. Ensure the Log history to file checkbox is ticked and set the path to the directory mentioned earlier. Uncheck the box to stop logging when data exceeds X MB, the program will deal with this automatically by clearing logs after consuming the relevant data. Apply these settings and the Afterburner setup is done. If you want to monitor different properties than those listed above then the code will need customising to produce graphs for these following the same methods shown in it.

The next step would be to set up where the window should open, for me I wanted it to open on my left most monitor in fullscreen by default but this can be changed. To change the positioning and size of the window you can change these lines:

```
w = 720
h = 457
root.overrideredirect(True)
root.geometry('%dx%d+%d+%d' % (w,h,-2648,77))
```
Where w and h correspond to the width and height. Overridedirect controls whether the window manager at the top is shown or not (True means not shown). The seemingly random numbers in the root.geometry line correspond to the x and y coordinates of the monitor I wanted to display on. I was using a three monitor setup with the target monitor the leftmost. I found these x and y coorindates by using

```
root.winfo_x()
root.winfo_y()
```

while the window was in fullscreen mode on the target display, this gave me the coordinates used to open on this monitor each time but can be adjusted for your setup.

From here, as long as you have updated your graphs if you are recording different data, you can compile with auto-py-to-exe. Don't forget to add Icon3.ico, Invisible.vbs and Restart.bat to the output folder where the Monitor.exe file is. The executable will then function as expected.

If the program cannot find any data being logged it will assume there is a bug and restart itself using Invisible.vbs and Restart.bat, using this method prevents any pop-ups or focus stealing events so it can fix itself while you carry on using your system. Usually if this occurs once it fixes the issue because the software tried to read data faster than it was being written and the close gave it time to update the file with new information. If this fix did not work however the program will try again up to 10 times over the course of a minute. If it is still not working the program will quit and wait for a manual fix and re-launch by the user, e.g. Msi Afterburner may have stopped logging unexpectedly. Generally the problem is fixed after one background restart. If you want to adjust the number of restart attempts or timing between attempts this can be edited in Invisible.vbs and Restart.bat respectively.
