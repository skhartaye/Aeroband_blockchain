with open('main/views.py', 'r') as file:
    content = file.read()

# Replace all instances of the ammonia threshold pattern
content = content.replace("'ammonia': {'warning': (1, 0.1), 'alert': (2, 0.05)},", 
                          "'ammonia': {'warning': (1, None), 'alert': (2, None)},")

with open('main/views.py', 'w') as file:
    file.write(content)

print("Ammonia thresholds updated successfully!") 