<h1 align="center" >About</h1>
This is a work in progress tool for the Mario Kart Scene, currently featuring:   

-  Automated Scoreboard for 8dx Lounge, Teammodes 2v2, 3v3, 4v4
-  6v6 works aswell, requires a little Setup for special Clan-Tags, refer to the Tips below
-  [You can Download the Program from here](https://github.com/Fobse/mk8dx-Utility/releases)



<h2 align="center" >OBS</h2>

Open the program, add a Window Capture to your scene in OBS, select the window "Scoreboard OBS Cleanfeed" and apply it. After, right click your new Window Capture in your scene and select "Filter". Add an Effectfilter with the + on the bottom left, choose Chroma Key. Set the Key-Color to "green" (should be the default) and apply. Done!


<h1 align="center" >Controls and Tips</h1>
<h6 align="center" >Here you will find Information and Knowledge about this program and how it works. Refer to this place if you run into issues, this will be updated as i make changes</h6>


<h3 align="center" >General Stuff</h3>

Team-Tag1 will be shown in golden color on the Scoreboard

The results of detection will always be shown in the tab "Process"

The program currently only supports english language, so only Romanian letters and simple symbols (e.g. (),",[],/)


<h3 align="center" >Setting Up</h3>

Go into the Tab "Video-Setup" and press the Button. The program will search for 10 external Video Devices connected to your Computer, list them and show the active Device below. If your Capture Card is not shown immediatly, select the other Devices from the dropdown list


<h3 align="center" >Automatic Mode</h3>
<h6 align="center" >Important Note: This program does not read any of the numbers on the Scoreboard, it only reads from the namefield and applies scores based on locations. Meaning, this program only works race by race and needs every races Scoreboard. Make sure to take Screenshots at the end of a race, before the Scoreboard is sorted</h6>

The "Start" Button will be activated, once you connected your Capture Card and applied the Team-Tags

The program triggers once it "sees" the 12th player and after a succesful trigger, it will be set on cooldown for 120 seconds

Feel free to test it with old Screenshots

Make sure to use the "Reset" Button before starting, as the memory will be saved within the program even after closing it. Reset will delete all Team-Tags, Scores and the Racecount from Memory and it will stop the Automatic Mode.


<h3 align="center" >Manual Trigger and 6v6</h3>

The Button "Manual Trigger" can be used anytime, even without Team-Tags, results will be shown.

As this program can not detect special symbols of Clantags, you need to use the "Manual Trigger" to get the "Automatic Mode" working for 6v6. Take a Screenshot and Run the "Manual Trigger" without adding Team-Tags. Look at the Results, all 6 players Tags of a team should be detected with the same letter(s). Use the Results to Apply the Team-Tags


<h3 align="center" >Score-Settings Tab</h3>
<h6 align="center" >In this Tab of the Program you can adjust the Scores of the Teams, changes are immediatly applied to the Table</h6>

You can use the "+" and "-" Button to the right of a Team to adjust the Score (Increments of 1 for each press)

"Missing" Points tell you that a Player could not be occupied to a team and theire Points are collected in the List. Make sure to remove the Points from "Missing" when you give them to a Team

A total Counter is running in the Background, it will tell you when the Points of all Teams do not match with the Race. You will see it when you adjust the Scores
