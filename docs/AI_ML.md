# AI/ML Pipeline & Explainable Decision Engine

## Machine Learning Subsystems

### 1. Computer Vision Quality Engine
- **Blur Detection**: Laplacian Variance $\text{Var}(\Delta I)$. Threshold $\ge 100.0$ for sharp text edges.
- **Glare & Exposure**: Luminance histogram bin analysis for overexposed pixels ($>240$) and underexposed pixels ($<15$).

### 2. Digital Artifact & Tamper Detection
- **Moire Frequency Spectrum**: 2D Fast Fourier Transform (FFT) power spectrum analysis. High frequency peak energy $>0.05$ flags screen photograph captures.
- **Edge Noise Density**: Canny edge detector density $>25\%$ flags copy-paste digital editing splices.

### 3. OCR & Field Extraction Pipeline
- Provider abstractions for AWS Textract ID Analysis and local Tesseract/Regex fallback engines.

### 4. Facial Matching & 3D Liveness
- 128D facial feature embedding distance calculation. Threshold $\ge 80.0\%$ similarity required for face match.

### 5. Multi-Signal Scoring Equation
$$\text{RiskScore} = \text{Clamp}_{0}^{100}\left( P_{\text{quality}} + P_{\text{ocr}} + P_{\text{tamper}} + P_{\text{liveness}} + P_{\text{facematch}} + P_{\text{mismatch}} \right)$$

Decision Outcomes:
- $\text{RiskScore} \le 20.0 \implies \mathbf{AUTO\_APPROVE}$
- $20.0 < \text{RiskScore} \le 75.0 \implies \mathbf{MANUAL\_REVIEW}$
- $\text{RiskScore} > 75.0 \implies \mathbf{REJECT}$
