# 🛡️ Security Policy

This document describes the security practices, supported versions, and vulnerability reporting process for this project.

The project is developed with a strong focus on **security, privacy, and responsible data handling**, following industry best practices and applicable data protection regulations.

---

## 🚀 Supported Versions

The following versions currently receive **security updates and maintenance**:

| Version   | Status          | Notes                             |
| --------- | --------------- | --------------------------------- |
| **5.1.x** | ✅ Supported     | Recommended for new installations |
| 5.0.x     | ❌ Not Supported | Legacy version                    |
| **4.0.x** | ✅ Supported     | Long-Term Support (LTS)           |
| < 4.0     | ❌ Not Supported | End of life                       |

> ⚠️ We strongly recommend always running the **latest supported version** to ensure that the most recent security patches and improvements are applied.

---

## ⚖️ Data Protection and Compliance (LGPD)

This project is developed with awareness of **data protection and privacy regulations**, including the **Brazilian General Data Protection Law (LGPD – Law No. 13.709/2018)**.

The system follows security and privacy principles such as:

* **Data Minimization** – Only the necessary data should be collected and processed.
* **Purpose Limitation** – Data must only be used for its intended purpose.
* **Transparency** – Users should be aware of how their data is handled.
* **Confidentiality** – Sensitive data must be protected through secure practices.
* **Integrity and Security** – Measures are implemented to prevent unauthorized access or data leaks.

Where applicable, developers and system administrators should ensure compliance with local privacy laws when deploying this software.

---

## 📢 Reporting a Vulnerability

If you discover a **security vulnerability**, please report it responsibly.

For security reasons, **do not open public GitHub issues** for vulnerabilities.

Instead, report the issue privately by contacting:

📧 [security@yourproject.com](mailto:security@yourproject.com)

Please include the following information in your report:

* A clear description of the vulnerability
* Steps to reproduce the issue
* The potential impact of the vulnerability
* Any suggested mitigation or fix (if available)

Responsible disclosure helps protect users and allows vulnerabilities to be resolved safely.

---

## 🔄 Vulnerability Response Process

Once a vulnerability report is received, the following process will be followed:

1. **Acknowledgement**
   The security team will acknowledge receipt of the report within **72 hours**.

2. **Investigation**
   The vulnerability will be reviewed and validated.

3. **Mitigation and Fix**
   If confirmed, a fix will be developed and released as soon as possible for supported versions.

4. **Security Advisory**
   A security advisory may be published after the issue has been resolved.

---

## 🔒 Security Best Practices

Developers and contributors should follow these security practices:

* Never expose **passwords, tokens, or private keys** in repositories.
* Store sensitive configuration using **environment variables**.
* Keep project **dependencies updated** to avoid known vulnerabilities.
* Avoid storing or logging **sensitive personal data** unnecessarily.

---

## ⚖️ Legal Disclaimer

Although this software is designed with security and privacy considerations in mind, **the organizations and individuals deploying this software are responsible for ensuring compliance with applicable data protection laws**, including the **LGPD** and any other relevant regulations in their jurisdiction.
