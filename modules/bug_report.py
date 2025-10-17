"""
Bug Report Generator Module for Synthalingua

Generates comprehensive system information reports for debugging and bug reporting.
Includes detection of frozen/portable mode and lists bundled files.
"""

import datetime
import platform
import sys
import os
import subprocess
import json
from pathlib import Path
from colorama import Fore, Style


def generate_bug_report():
    """Generate a comprehensive bug report with system information, Python environment, and Synthalingua details."""
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"bugreport_info_{timestamp}.txt"
    
    print(f"{Fore.CYAN}Generating comprehensive bug report...{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Output file: {filename}{Style.RESET_ALL}")
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("SYNTHALINGUA BUG REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append("")
    
    # Detect if running in frozen/portable mode
    is_frozen = getattr(sys, 'frozen', False)
    report_lines.append("EXECUTION MODE")
    report_lines.append("-" * 40)
    if is_frozen:
        report_lines.append("Mode: Frozen/Portable (PyInstaller)")
        report_lines.append(f"Executable Path: {sys.executable}")
        
        # Try to find _internal directory
        if hasattr(sys, '_MEIPASS'):
            report_lines.append(f"Temp Extraction Path: {sys._MEIPASS}")
        
        # List files in the executable directory
        exe_dir = Path(sys.executable).parent
        report_lines.append(f"Executable Directory: {exe_dir}")
        
        try:
            exe_files = sorted([f for f in exe_dir.iterdir() if f.is_file()])
            exe_dirs = sorted([d for d in exe_dir.iterdir() if d.is_dir()])
            
            report_lines.append(f"Bundled Files in Executable Directory: {len(exe_files)} files, {len(exe_dirs)} directories")
            
            # List all files
            for file in exe_files[:20]:  # Show first 20 files
                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    report_lines.append(f"  {file.name} ({size_mb:.2f} MB)")
                except:
                    report_lines.append(f"  {file.name}")
            
            if len(exe_files) > 20:
                report_lines.append(f"  ... and {len(exe_files) - 20} more files")
            
            # List directories
            report_lines.append("Bundled Directories:")
            for dir in exe_dirs[:10]:  # Show first 10 dirs
                try:
                    dir_items = len(list(dir.iterdir()))
                    report_lines.append(f"  {dir.name}/ ({dir_items} items)")
                except:
                    report_lines.append(f"  {dir.name}/")
            
            if len(exe_dirs) > 10:
                report_lines.append(f"  ... and {len(exe_dirs) - 10} more directories")
            
            # If _internal directory exists, list some of its contents
            internal_dir = exe_dir / '_internal'
            if internal_dir.exists():
                report_lines.append("")
                report_lines.append("_internal Directory Contents (sample):")
                try:
                    internal_files = sorted([f for f in internal_dir.iterdir() if f.is_file()])[:15]
                    internal_dirs = sorted([d for d in internal_dir.iterdir() if d.is_dir()])[:10]
                    
                    for file in internal_files:
                        try:
                            size_mb = file.stat().st_size / (1024 * 1024)
                            report_lines.append(f"  {file.name} ({size_mb:.2f} MB)")
                        except:
                            report_lines.append(f"  {file.name}")
                    
                    for dir in internal_dirs:
                        report_lines.append(f"  {dir.name}/")
                    
                    total_internal = len(list(internal_dir.iterdir()))
                    shown = len(internal_files) + len(internal_dirs)
                    if total_internal > shown:
                        report_lines.append(f"  ... and {total_internal - shown} more items")
                        
                except Exception as e:
                    report_lines.append(f"  Error listing _internal: {e}")
                    
        except Exception as e:
            report_lines.append(f"Error listing bundled files: {e}")
    else:
        report_lines.append("Mode: Source/Development (Python script)")
        report_lines.append(f"Script Path: {sys.argv[0]}")
    
    report_lines.append("")
    
    # System Information
    report_lines.append("SYSTEM INFORMATION")
    report_lines.append("-" * 40)
    try:
        report_lines.append(f"OS: {platform.system()} {platform.release()}")
        report_lines.append(f"OS Version: {platform.version()}")
        report_lines.append(f"Architecture: {platform.architecture()}")
        report_lines.append(f"Machine: {platform.machine()}")
        report_lines.append(f"Processor: {platform.processor()}")
        
        # CPU Info
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            report_lines.append(f"CPU Cores: {cpu_count} physical, {cpu_count_logical} logical")
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                report_lines.append(f"CPU Frequency: {cpu_freq.current:.1f} MHz (max: {cpu_freq.max:.1f} MHz)")
        except:
            report_lines.append("CPU Info: Unable to retrieve")
        
        # Memory Info
        try:
            import psutil
            mem = psutil.virtual_memory()
            report_lines.append(f"Total Memory: {mem.total // (1024**3)} GB")
            report_lines.append(f"Available Memory: {mem.available // (1024**3)} GB")
        except:
            report_lines.append("Memory Info: Unable to retrieve")
        
        # Disk Info
        try:
            import psutil
            disk = psutil.disk_usage('/')
            report_lines.append(f"Disk Space: {disk.total // (1024**3)} GB total, {disk.free // (1024**3)} GB free")
        except:
            report_lines.append("Disk Info: Unable to retrieve")
            
    except Exception as e:
        report_lines.append(f"System Info Error: {e}")
    
    report_lines.append("")
    
    # Python Information
    report_lines.append("PYTHON INFORMATION")
    report_lines.append("-" * 40)
    report_lines.append(f"Python Version: {sys.version}")
    report_lines.append(f"Python Executable: {sys.executable}")
    report_lines.append(f"Python Path: {sys.path[:3]}...")  # First 3 paths
    
    # Virtual Environment
    try:
        venv = os.environ.get('VIRTUAL_ENV', 'None')
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'None')
        report_lines.append(f"Virtual Environment: {venv}")
        report_lines.append(f"Conda Environment: {conda_env}")
    except:
        report_lines.append("Environment Info: Unable to retrieve")
    
    report_lines.append("")
    
    # Installed Packages (only if not frozen, as frozen mode doesn't have pip)
    if not is_frozen:
        report_lines.append("INSTALLED PYTHON PACKAGES")
        report_lines.append("-" * 40)
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in sorted(packages, key=lambda x: x['name'].lower()):
                    report_lines.append(f"{pkg['name']}=={pkg['version']}")
            else:
                report_lines.append("Failed to get package list")
                report_lines.append(f"Error: {result.stderr}")
        except Exception as e:
            report_lines.append(f"Package list error: {e}")
        
        report_lines.append("")
    else:
        report_lines.append("PYTHON PACKAGES")
        report_lines.append("-" * 40)
        report_lines.append("Package list not available in frozen/portable mode")
        report_lines.append("Dependencies are bundled in the executable")
        report_lines.append("")
    
    # GPU Information
    report_lines.append("GPU INFORMATION")
    report_lines.append("-" * 40)
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            for i, gpu in enumerate(gpus):
                report_lines.append(f"GPU {i}: {gpu.name}")
                report_lines.append(f"  Memory: {gpu.memoryTotal} MB")
                report_lines.append(f"  Driver: {gpu.driver}")
        else:
            report_lines.append("No GPUs detected")
    except Exception as e:
        report_lines.append(f"GPU Info Error: {e}")
    
    # CUDA Info
    try:
        import torch
        report_lines.append(f"PyTorch CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            report_lines.append(f"CUDA Version: {torch.version.cuda}")
            report_lines.append(f"GPU Count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                report_lines.append(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    except:
        report_lines.append("PyTorch/CUDA Info: Not available")
    
    report_lines.append("")
    
    # Synthalingua Information
    report_lines.append("SYNTHALINGUA INFORMATION")
    report_lines.append("-" * 40)
    try:
        from modules.version_checker import version
        report_lines.append(f"Synthalingua Version: {version}")
    except:
        report_lines.append("Version: Unable to retrieve")
    
    # Current working directory and important files
    report_lines.append(f"Current Working Directory: {os.getcwd()}")
    
    # Check for important files
    important_files = [
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        'demucs_python_path.txt',
        'synthalingua.spec',
        'set_up_env.spec'
    ]
    
    report_lines.append("Important Files Present:")
    for file in important_files:
        exists = Path(file).exists()
        report_lines.append(f"  {file}: {'✓' if exists else '✗'}")
    
    # Models directory
    models_dir = Path('models')
    if models_dir.exists():
        model_files = list(models_dir.glob('*'))
        report_lines.append(f"Models Directory: {len(model_files)} files")
        for model in sorted(model_files)[:10]:  # Show first 10
            report_lines.append(f"  {model.name}")
        if len(model_files) > 10:
            report_lines.append(f"  ... and {len(model_files) - 10} more")
    else:
        report_lines.append("Models Directory: Not found")
    
    report_lines.append("")
    
    # Environment Variables (relevant ones)
    report_lines.append("RELEVANT ENVIRONMENT VARIABLES")
    report_lines.append("-" * 40)
    relevant_env_vars = [
        'PATH',
        'PYTHONPATH',
        'PYTHONHOME',
        'VIRTUAL_ENV',
        'CONDA_DEFAULT_ENV',
        'CUDA_VISIBLE_DEVICES',
        'TORCHAUDIO_USE_BACKEND_DISPATCHER',
        'TORIO_USE_FFMPEG',
        'PYTHONIOENCODING'
    ]
    
    for var in relevant_env_vars:
        value = os.environ.get(var, 'Not set')
        if len(str(value)) > 100:  # Truncate long values
            value = str(value)[:97] + "..."
        report_lines.append(f"{var}: {value}")
    
    report_lines.append("")
    
    # Audio Devices
    report_lines.append("AUDIO DEVICES")
    report_lines.append("-" * 40)
    try:
        import speech_recognition as sr
        mic_list = sr.Microphone.list_microphone_names()
        report_lines.append(f"Available Microphones: {len(mic_list)}")
        for i, mic in enumerate(mic_list[:5]):  # Show first 5
            report_lines.append(f"  {i}: {mic}")
        if len(mic_list) > 5:
            report_lines.append(f"  ... and {len(mic_list) - 5} more")
    except Exception as e:
        report_lines.append(f"Audio Devices Error: {e}")
    
    report_lines.append("")
    
    # Network Information
    report_lines.append("NETWORK INFORMATION")
    report_lines.append("-" * 40)
    try:
        import socket
        hostname = socket.gethostname()
        report_lines.append(f"Hostname: {hostname}")
        try:
            ip = socket.gethostbyname(hostname)
            report_lines.append(f"IP Address: {ip}")
        except:
            report_lines.append("IP Address: Unable to retrieve")
    except Exception as e:
        report_lines.append(f"Network Info Error: {e}")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF BUG REPORT")
    report_lines.append("=" * 80)
    
    # Write to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"{Fore.GREEN}Bug report generated successfully: {filename}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Please attach this file when reporting bugs.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error writing bug report: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Report content:{Style.RESET_ALL}")
        print('\n'.join(report_lines))
