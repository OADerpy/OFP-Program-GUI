# OFP-Program-GUI
Program to automate filling out the OSMAA Operational Flight Plan

## How to install this program
### 1. Download zipped file
At the top of this page Click the green button labeled "code". Then Click "Download ZIP".
![image](https://github.com/user-attachments/assets/76a53753-5966-45e8-b020-3af8077f92e2)

Once downloaded, move the file to where you want the program to be. For example on your desktop. 
Then right-click the file and select an option similar to "Extract files".

### 2. Download Python3
This project is written in python, so in order to use it you will need to install it.

**!! This program does not work with python versions 3.14 and newer. I reccomend using python version 3.13.5 for this program !!**

Go to https://www.python.org/downloads/ and click the download button
![image](https://github.com/user-attachments/assets/031b6f65-386e-4210-9851-44c2b43253bf)

After downloading, you will need to run the file in order to start the installation process.

**!! It is important that you select the option "Add python.exe to PATH" during the installation. !!**
![image](https://github.com/user-attachments/assets/859278b4-271e-44d9-97ae-9fa3449145f9)


### 3. Download Required Libraries
Now that you have installed python, the last thing to do is to install the libraries required for this project.

First you will need to open the command prompt (Or the terminal if you are using a MAC).
On windows: Go to the bottom left and search for "cmd". Then click to open the command prompt.
![image](https://github.com/user-attachments/assets/e51ce63e-0106-4d81-9cd5-3f95600f0418)

You will need to copy-paste each one of the 3 lines below into the command prompt and then press enter

pip install bs4

pip install PyPDFForm

pip install dearpygui

You should now be able to click on "main.py" in order to start the program.
![image](https://github.com/user-attachments/assets/5125b5e4-d41e-4ebe-915a-35dba51e00c8)


### If you have any trouble with installing feel free to send me a message on discord:
oa_derpy


## How to use this program
1. Log in on your computer on [plan.foreflight.com](https://plan.foreflight.com/)
1. Open the flight's navlog page
2. Right click the background of the page -> view frame source
3. Ctrl + a -> crl + c
4. Start the program by running 'main.py'
5. Paste raw text into the top left box of the program labeled "Navlog Input"
6. Press Extract, and fill in all the remaining information on the right side of the window
7. When you are done filling in the remaining information, press "Export as PDF" to save the file.
8. Go into the folder "output" to find your generated OFP
