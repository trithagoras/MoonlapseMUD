import sys, json
from PIL import Image

if len(sys.argv) not in (2, 3):
  print('Script takes 2 positional arguments: input image path and output file name.')
  print('Script can also take 1 positional argument: input image path and output will take same name.')
  sys.exit()

elif len(sys.argv) == 2:
  f_out = sys.argv[1] + '.json'
elif len(sys.argv) == 3:
  f_out = sys.argv[2]

image = Image.open(sys.argv[1])
width, height = image.size
blackAndWhite = image.convert("1")

values = list(blackAndWhite.getdata())

output = {
  "walls": [],
  "size": [height, width]
}

for row in range(0, height):
  for column in range(0, width):
    if values[row * width + column] == 0:
      output['walls'].append([row, column])

with open(f_out, 'w') as file:
    json.dump(output, file)