# RAS User interface

## Overview
Converts natural language to a yaml file that can be used to generate a behavior tree.

## api_calls.py
Takes input in Natural language and then converts it into a linear sequence of modules, with the appropriate parameters. 

## asset_mapper.py
Makes queries against container_assets.csv to find the lab containers satisfying all the necessary constraints. Returns the unique ids of the matched containers. (fuzzy matching to be added soon)

## pose_fetcher.py
Once the unique ids of the containers are obtained, the locations are obtained from container_assets.csv. The script also make updates to locations stored in container_assets.csv after place operations. Update this logic when adding more actions.

## main.py
Coordinates the previous three scripts in sequence to convert natural language to the following yaml format. 
```{yaml}
Poses:
  pose1:
    x: 0.9
    y: 0.0
    z: 0.0
    roll: 0.0
    pitch: 0.0
    yaw: 1.0
  pose2:
    x: 0.5
    y: 0.0
    z: 0.0
    roll: 0.0
    pitch: 0.0
    yaw: 1.0
  pose3:
    x: 1.0
    y: 2.0
    z: 3.0
    roll: 0.0
    pitch: 0.0
    yaw: 1.0
targets:
- pose1
- grasp
- pose2
- 1.57
- -1.57
- pose3
- release
```
# container_assets.csv
<img width="652" alt="image" src="https://github.com/user-attachments/assets/1581a238-3ef9-4781-9e18-ef40bb0569ce">





### Notes
- Right now, this model uses GPT4o for parsing the natural language input. It will be replaced later with an open source LLM suited to the purpose, along with some checks to ensure consistent performance.

## Contributing
Feel free to open issues or pull requests if you have suggestions or improvements. Contributions are always welcome!

