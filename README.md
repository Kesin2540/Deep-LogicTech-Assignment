# Deep-LogicTech-Assignment

This Python assignment implements a service that returns the latest 6 stories from Time.com. Since the site lacks a dedicated "latest stories" section, the solution fetches the latest 6 articles from multiple sections—Politics, World, Health, Climate, Science, Entertainment, and Ideas—and selects the 6 most recent based on publication time.

Using only Python’s standard libraries (urllib, re, json, threading, http.server), the code parses HTML to extract article titles, links, and publication times. Multithreading speeds up fetching, and the final data is served as a JSON array via a simple GET API

```bash
http://localhost:8080/getTimeStories
```
This assignment demonstrates basic HTML processing, concurrent data fetching, and JSON response handling without external libraries, fulfilling the one-day task requirements.
