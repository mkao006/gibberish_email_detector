import csv
import random
from faker import Faker

fake = Faker()

def generate_legit_email():
    # legitimate email: firstname.lastname@domain.com or firstname.lastname123@domain.com
    first = fake.first_name().lower()
    last = fake.last_name().lower()
    domain = fake.domain_name()
    
    # 50% chance to add a number
    if random.choice([True, False]):
        number = random.randint(1, 9999)
        return f"{first}.{last}{number}@{domain}"
    
    return f"{first}.{last}@{domain}"

def generate_gibberish_email():
    # gibberish email: fdasfjaklsd@gmail.com
    # Generating a random string of 8-15 characters, including numbers
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    local_part = ''.join(random.choices(chars, k=random.randint(8, 15)))
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])
    return f"{local_part}@{domain}"

def generate_keyword_spam():
    # keyword spam: win.free.money@gmail.com
    keywords = ["win", "prize", "offer", "discount", "free", "urgent", "money"]
    selected = random.sample(keywords, k=random.randint(2, 3))
    
    # 50% chance to add a number suffix
    if random.choice([True, False]):
        selected.append(str(random.randint(100, 999)))
        
    local_part = '.'.join(selected)
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])
    return f"{local_part}@{domain}"

def main(count=120):
    import sys
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    data = []
    # Generate ham
    for _ in range(count // 3):
        data.append((generate_legit_email(), 0))
    # Generate gibberish spam
    for _ in range(count // 3):
        data.append((generate_gibberish_email(), 1))
    # Generate keyword spam
    for _ in range(count // 3):
        data.append((generate_keyword_spam(), 1))
    
    random.shuffle(data)
    
    import os
    os.makedirs('data', exist_ok=True)
    with open('data/emails.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'label'])
        writer.writerows(data)
    print(f"Generated {count} emails in data/emails.csv")

if __name__ == "__main__":
    main()
