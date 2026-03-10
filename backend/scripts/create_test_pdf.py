from fpdf import FPDF
import os

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

text = """
Zoho Interview Experience

The first round was a technical interview. The interviewer was very nice.
He asked me: Can you explain the difference between a process and a thread?
Then we moved on to coding.
He asked me to write a Java program to reverse a linked list.
I also had some HR questions like where do you see yourself in 5 years?
What are the four pillars of Object-Oriented Programming (OOP)?
Describe the internal working of a HashMap in Java.
Finally, what is the time complexity of QuickSort in the worst case?
"""

pdf.multi_cell(0, 10, txt=text)
os.makedirs("uploads/feedback", exist_ok=True)
pdf.output("uploads/feedback/ZOHO_FB.pdf")
print("PDF created successfully at uploads/feedback/ZOHO_FB.pdf")
