import numpy as np
import matplotlib.pyplot as plt

# Generate data
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# Create the plot
plt.plot(x, y)
plt.title("Sine Curve")
plt.xlabel("x")
plt.ylabel("sin(x)")
plt.grid(True)

# Show the plot
plt.show()
