import matplotlib.pyplot as plt; import numpy as np
x = np.linspace(0.1, 10, 400)
y = np.exp(np.log(x))
plt.plot(x, y)
plt.title('y = e^log(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.savefig('final_math_test.png'); plt.close()