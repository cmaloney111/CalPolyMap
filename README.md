# SmartRouteFinder

This README provides the necessary instructions to set up and run SmartRouteFinder locally. Follow the steps below to install the dependencies, run the application, and access the web interface.

## Prerequisites

- [Anaconda](https://www.anaconda.com/products/individual) (for managing Python environments)
- [Python](https://www.python.org/) 3.7+ (if not installed with Anaconda)
- A web browser to access the application
- So far, tested on MacOS 15.1, Windows 10, and Windows 11 (along with WSL).

## Step 1: Install the Conda Environment

1. Clone the repository to your local machine (if you haven't already).
   
   ```bash
   git clone https://github.com/cmaloney111/CalPolyMap.git
   cd CalPolyMap
   ```

2. Activate the conda environment
   ```bash
   conda env create -f environment.yml
   conda activate CalPolyMap
   ```

## Step 2: Running the Application
After setting up the environment, you can run the application by executing the following command:

   ```bash
   python app.py
   ```

Once the application starts, it will be accessible via a web interface at http://127.0.0.1:8050


Open this URL in your web browser to interact with the application.

## Step 3: Handling the 3D Reconstruction File
The file output.ply, which contains the 3D reconstruction data, is not included in this repository due to its large size. Contact me separately if you would like this file

# Troubleshooting
Issue: The application doesn't start after running python app.py.

Solution: Ensure that the Conda environment is activated correctly and all dependencies are installed.

Issue: Unable to access the web interface at http://127.0.0.1:8050.

Solution: Ensure that no other applications are using port 8050. You can specify a different port by setting the port parameter in app.py.
