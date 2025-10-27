# Paper View

<p align="center">
      <img src="./assets/readme_images/index.png" alt="Paper View" width="800"/>
</p>

<p align="center">
  <a href="https://github.com/yyccR/paper-view"><img alt="GitHub stars" src="https://img.shields.io/github/stars/yyccR/paper-view?style=social"></a>
  <a href="https://github.com/yyccR/paper-view/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/yyccR/paper-view"></a>
  <a href="https://github.com/yyccR/paper-view/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/yyccR/paper-view"></a>
  <img alt="Django" src="https://img.shields.io/badge/Django-4.2.7-green.svg">
  <img alt="Vue" src="https://img.shields.io/badge/Vue-3.x-brightgreen.svg">
</p>

<p align="center">
  <a href="./README_CN.md"><img alt="简体中文版自述文件" src="https://img.shields.io/badge/简体中文-d9d9d9"></a>
  <a href="./README_EN.md"><img alt="English README" src="https://img.shields.io/badge/English-d9d9d9"></a>
</p>

## 🌟 Introduction

Paper View is a cutting-edge **Paper Visual Reading System** designed for researchers, students, and AI enthusiasts. Built with modern web technologies, Paper View transforms the way you interact with academic papers by combining powerful search capabilities, intuitive PDF viewing, and rich data visualization tools. Whether you're exploring arXiv's vast repository of 2.8+ million papers or analyzing your own research documents, Paper View provides an elegant and efficient workflow.

## ✨ Key Features

*   **📚 arXiv Paper Support:** Access the complete arXiv database across all categories, with 2.8+ million papers
*   **📊 Rich Visualization:** 50+ chart templates for multi-dimensional data and relationship visualization
*   **⚡ Real-time Updates:** Daily synchronization with arXiv to capture the latest research publications
*   **📄 PDF Management:** Upload, view, and analyze PDFs with built-in viewer and reference extraction
*   **🤖 AI-Powered:** Integration with multiple LLM providers for intelligent content analysis


## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:

*   **Conda** (Anaconda or Miniconda)
*   **MySQL 5.7+ or 8.0+**
*   **Node.js 16+ & npm** (optional, for frontend development)
*   **Git**

### One-Click Installation

```bash
# Clone the repository
git clone https://github.com/yyccR/paper-view.git
cd paper-view

# Run the installation script
chmod +x install.sh
./install.sh
```

The installation script will automatically:
- ✅ Check prerequisites (Conda, MySQL)
- ✅ Create Conda environment with Python 3.10
- ✅ Install all Python dependencies
- ✅ Create `.env` configuration file
- ✅ Set up MySQL database
- ✅ Run database migrations
- ✅ Install frontend dependencies (if Node.js is available)

### Configuration

After installation, edit the `.env` file to configure your settings:

```env
# Database Configuration
DB_NAME=paper_view
DB_USER=root
DB_PASSWORD=your_password

# Optional: LLM API Keys
OPENAI_API_KEY=sk-your-openai-api-key
QWEN_API_KEY=sk-your-qwen-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
# ... other API keys as needed
```

### Start the Application

First, make sure you have activated the Conda environment:

```bash
conda activate paper-view
```

**Development Mode (Recommended)**

Run frontend and backend with hot reload:

```bash
./start.sh dev
```

**Production Mode**

Run as a single Django application:

```bash
./start.sh
```

- 👉 Frontend: `http://localhost:9521`




## 📜 License

Paper View is licensed under a modified version of the Apache License 2.0, with the following additional conditions:

1.  **Commercial Usage Authorization:** If you want to use Paper View in your company's commercial products, regardless of whether there is a profit-making behavior or not, you must obtain written authorization from the producer of Paper View. Otherwise, using the Paper View source code to build and release your products is not allowed.

2.  **LOGO and Copyright Information:** When integrating the Paper View source code into your products or interfaces, you shall not remove or modify the LOGO and copyright information of the Paper View application.

3.  **Contributor Agreement:** As a contributor, you should agree that:
    - a. The producer can adjust the open-source agreement to be either more stringent or more lenient as deemed necessary.
    - b. The code you contribute may be used for commercial purposes, including but not limited to cloud business operations.

Except for the specific conditions mentioned above, all other rights and restrictions are in accordance with the Apache License 2.0. Detailed information about the Apache License 2.0 can be found at http://www.apache.org/licenses/LICENSE-2.0.

The unique interface design and interactive elements of Paper View are protected by relevant patents and intellectual property laws.

---

<p align="center">Made with ❤️ by the Paper View Team</p>
<p align="center">© 2025 Paper View. All rights reserved.</p>
