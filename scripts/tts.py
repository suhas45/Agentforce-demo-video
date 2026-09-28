import sys, soundfile as sf
from kokoro_onnx import Kokoro
K = sys.argv[1]
k = Kokoro(f"{K}/kokoro-v1.0.onnx", f"{K}/voices-v1.0.bin")
S = ["For the customer, this means a faster and more convenient way to resolve an exchange request through a simple conversation.",
"For C Fashion, Agentforce helps automate repetitive exchange interactions and reduces the need for service teams to manually handle these requests.",
"The customer simply explains what they need, and the agent takes care of the rest.",
"C Fashion with Agentforce — making product exchanges simple, conversational, and convenient."]
for i, s in enumerate(S, 1):
    a, sr = k.create(s, voice="af_heart", speed=0.95, lang="en-us")
    sf.write(f"audio/s{i}.wav", a, sr)
    print(i, len(a)/sr)
