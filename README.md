# Phbot Event-Based Alchemy Plugin

Event-driven alchemy plugin for Phbot.

Triggers the next fuse immediately after receiving the server result instead of using a fixed delay.

Built for private servers that support instant fuse.

<br>

# Installation

Place the Alchemist.py file in Plugins folder in your phbot directory.

<br>

# ⚠️ Warning

This plugin does **not** check the current item stats before fusing.  
If your item is already at or above your target, it will still attempt to fuse instead of aborting.