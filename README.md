<h1>isi_tools</h2>
Read this README in its entirety before working with isi_tools.

<h3>What is isi_tools?</h3>
isi_tools is a library of standalone scripts for Powerscale(isilon) admins... inspired by crowdsourced ideas and rage.<br /><br />isi_tools is meant to be used as-is or serve as an example of the "possible" for system administrators of the Dell EMC Powerscale platform. Feel free to reference or modify isi_tools and create your own library of things you would like to automate on Powerscale. Each script is meant to be standalone without any external requirements. You can just pull a single file you need and use it entirely on its own.

<h3>Why is isi_tools useful?</h3>
isi_tools is useful for the folks interested in automating administrative tasks for managing a Powerscale environment. It can be a daunting task at first, but with the examples within isi_tools you can quickly start to understand just how simple it can be. Use this as your own or use it as an example to create your own toolset!<br /><br />

If you feel this is a bit advanced for your current understanding of how to interact with the Powerscale API, check out <a href="https://github.com/j-sims/IsilonAPIQuickStartGuidePython">IsilonAPIQuickStartGuidePython</a> for some great examples!

<h3>Getting started with isi_tools</h3>
1. Clone the repo and run 'pip install -r requirements.txt'<br /><br />
2. isi_tools starts with a decision on whether you want to run config.py and supply your user name and password. This is your personal choice. BEWARE: your password will be stored base64 encoded in a file called creds.json within isi_tools directory. This will allow you to run any "isi_" prefixed tool without supplying credentials each time. If you run config.py and then want to delete creds.json after you're done, then go ahead! You have the choice to run it next time you interact with the repo or not.<br /><br />
3. isi_tools has menu driven tools which require user input. These are prefixed with "isi_".<br />isi_tools also has tools which take arguments when they are executed so they don't require any user input. These are not prefixed with "isi_" AND they require config.py to get credentials otherwise it will prompt you.<br /><br />
4. Each tool has a '-h' switch to help with syntax. Example: python isi_snaplock.py -h<br /><br />
5. Each tool logs its interactions with the Powerscale API and whether it was successful or not in isi_tools.log. This is meant for you to be able to see historically what CRUD operations have occurred. If it gets too big, or if you do not want to keep it around. Delete it. It will regenerate.

<h3>Where can I get help?</h3>
Feel free to send a message to <a href="https://github.com/attack33">attack33</a>.

<h3>Contributors</h3>
isi_tools is maintained by <a href="https://github.com/attack33">attack33</a>.
