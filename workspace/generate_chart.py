import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0.1, 10, 400) # Start from 0.1 to avoid log(0)
y = np.exp(np.log(x))
plt.plot(x, y)
plt.title('y=e^log(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.grid(True)
plt.savefig('math_study.png')
plt.show()