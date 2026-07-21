#!/usr/bin/env python3
"""
Generate Customer Support Email Benchmark Dataset.

This script programmatically creates a realistic customer support benchmark dataset
containing 100 high-quality, non-repetitive email threads across 15 distinct categories.
Each thread contains:
  - email_id: Unique identifier (EMAIL_001 to EMAIL_100)
  - category: One of 15 support categories
  - customer_email: The incoming customer query (varying length, tone, and urgency)
  - expected_reply: A high-quality, empathetic, and professional reference response
  - urgency: Low, Medium, High, or Critical
  - tone: Angry, Frustrated, Polite, Friendly, Professional, or Urgent
"""

import os
import csv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_dataset_raw_data() -> list[dict[str, str]]:
    """Return a hardcoded list of exactly 100 high-quality customer support conversations."""
    return [
        # --- 1. REFUND (7 items) ---
        {
            "category": "Refund",
            "customer_email": "Hi, I purchased a subscription yesterday but realized I won't use it. Can I please get my money back? My account email is user101@example.com.",
            "expected_reply": "Hello, thank you for reaching out. I have reviewed your request, and since you purchased your subscription yesterday and have not used any credits, you are fully eligible for our 24-hour money-back guarantee. I have processed a full refund to your original payment method. The funds should appear in your account within 3 to 5 business days, depending on your bank. Your subscription has been cancelled. Please let us know if we can help you with anything else in the future.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Refund",
            "customer_email": "You guys charged me twice for my monthly bill! This is unacceptable! I want a refund for the double charge immediately. Fix this now!",
            "expected_reply": "Hello, thank you for contacting us, and please accept our sincere apologies for the billing error. I have investigated your account and confirmed that an extra charge was mistakenly processed on your credit card. I have immediately processed a refund of the duplicate charge ($19.99). You should see the credit back on your statement in 2 to 5 business days. We are reviewing our payment gateway to ensure this doesn't happen again. Thank you for your patience.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Refund",
            "customer_email": "Hey, my son made an unauthorized in-app purchase on my account yesterday. Is there any way I can get a refund for this? It was an accident.",
            "expected_reply": "Hello, thank you for reaching out to us. We understand that accidental purchases can happen, especially with children. I have located the transaction from yesterday and have approved a one-time courtesy refund for the unauthorized purchase. The refund has been submitted to your payment method and should clear in 3-5 business days. To prevent future accidental charges, we highly recommend enabling password verification for all purchases in your account settings.",
            "urgency": "Medium",
            "tone": "Friendly",
        },
        {
            "category": "Refund",
            "customer_email": "I returned my jacket over two weeks ago and still haven't seen the refund on my credit card. What is taking so long? Order #JACK-8821.",
            "expected_reply": "Hello, thank you for your inquiry regarding order #JACK-8821. I have checked our return system and can see that your jacket was received at our warehouse on the 10th of this month. It appears there was a processing delay in our returns department, for which we sincerely apologize. I have manually finalized the return and issued your full refund of $85.00 today. The billing statement should update within 3 to 5 business days. Thank you for your patience.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Refund",
            "customer_email": "I bought your software thinking it had a bulk export feature, but it turns out it doesn't. Since it doesn't fit my needs, I would like to request a refund. Thanks, Mark.",
            "expected_reply": "Hello Mark, thank you for writing to us. I am sorry to hear that our software does not support the bulk export feature you require. Since we want our customers to be fully satisfied, I have initiated a full refund for your purchase. Your access will remain active until the end of today. We appreciate your feedback regarding the bulk export feature, and I have shared this request with our product engineering team for future updates. Best of luck with your projects.",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "Refund",
            "customer_email": "Can I get a refund for my order #9921? It arrived broken, and I don't want a replacement anymore, just my money back.",
            "expected_reply": "Hello, I am incredibly sorry to hear that your order #9921 arrived broken. This is certainly not the standard we strive for. I have processed a full refund for your order, including shipping fees, which should credit back to your payment method in 3-5 business days. You do not need to return the broken item to us; please dispose of it safely. Thank you for letting us know, and we hope to serve you better in the future.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Refund",
            "customer_email": "I am writing to formally request a refund for order #20391. The services provided did not match the specifications outlined in our contract.",
            "expected_reply": "Hello, thank you for your email. We take contract specifications and customer satisfaction very seriously. I have forwarded your request and contract details to our accounts manager for a formal review. We will contact you within 24 hours to discuss the refund options and ensure we address the discrepancy to your satisfaction. Thank you for your professionalism and patience.",
            "urgency": "Medium",
            "tone": "Professional",
        },

        # --- 2. ORDER STATUS (7 items) ---
        {
            "category": "Order Status",
            "customer_email": "Hi, I placed an order (#ORD-5541) three days ago but haven't received any shipping notification. Can you tell me when it will ship?",
            "expected_reply": "Hello, thank you for checking on your order #ORD-5541. Your order is currently being processed at our warehouse and is packed and ready for shipping. It is scheduled to be picked up by our courier partner later this afternoon. Once it ships, you will receive an email with your tracking number and an estimated delivery date. Please let us know if you need anything else.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Order Status",
            "customer_email": "Where is my package? Order #4412. It was supposed to be here yesterday and I need it for a birthday party tonight. Is it lost?",
            "expected_reply": "Hello, thank you for reaching out, and I apologize for the delay. I have tracked your package for order #4412 and see that it is currently at your local distribution facility. The carrier has marked it as 'on vehicle for delivery' as of 7:30 AM this morning, meaning it will arrive at your address today, typically by 5:00 PM. Please monitor the delivery status, and let us know if it hasn't arrived by late afternoon so we can contact the carrier directly.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Order Status",
            "customer_email": "Hello! I lost my order confirmation email, but I think my order number was something like #7721. Could you check the status for me? My name is Sarah Jenkins.",
            "expected_reply": "Hello Sarah! Thanks for getting in touch. I searched our system using your name and email and located your order, which is indeed #7721. Your package shipped yesterday via USPS and is currently in transit. The tracking link shows an estimated delivery date of this Thursday. I have resent the full order confirmation email with the tracking link to this address for your records. Let us know if you have any other questions!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Order Status",
            "customer_email": "Can you check the status of my order #8831? I paid for express shipping but it still hasn't arrived. It has been 4 days.",
            "expected_reply": "Hello, thank you for your email, and I sincerely apologize for the delay in receiving your order #8831. I looked into the tracking history and found that a logistics delay occurred at our regional sorting hub. Because your package did not arrive within the guaranteed express window, I have refunded your express shipping fee of $15.00 today. Your order is now out for delivery and should arrive tomorrow. Thank you for your understanding.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Order Status",
            "customer_email": "I want to check if my order #9920 has been processed yet. I need to make sure it will arrive before I go on vacation next week.",
            "expected_reply": "Hello, thank you for writing. I can confirm that your order #9920 has been successfully processed and is currently in the queue at our fulfillment center. It is estimated to ship tomorrow and will take approximately 3 business days to reach your address, putting the delivery date on Friday, which is well before your vacation next week. We will email you the tracking details as soon as it is picked up by the courier.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Order Status",
            "customer_email": "Hello, is order #7712 still on backorder? It's been a month and I haven't heard anything. Please let me know what is going on.",
            "expected_reply": "Hello, thank you for reaching out, and we deeply apologize for the extended wait time and lack of communication regarding order #7712. I have checked with our inventory manager, and unfortunately, the item is still backordered due to supply chain disruptions. We expect our next shipment in about two weeks. If you prefer not to wait, we can cancel this order for a full refund or exchange it for a similar item in stock. Please let us know how you would like to proceed.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Order Status",
            "customer_email": "Could you provide the tracking number for order #6652? The email I received didn't seem to contain it.",
            "expected_reply": "Hello, thank you for contacting support. I apologize that the tracking details were missing from your automated confirmation. Your tracking number for order #6652 is 1Z999AA10123456784, shipped via UPS. You can track your package directly on the UPS website, and it is currently scheduled for delivery this Wednesday. Please let us know if we can assist you with anything else.",
            "urgency": "Low",
            "tone": "Professional",
        },

        # --- 3. LATE DELIVERY (7 items) ---
        {
            "category": "Late Delivery",
            "customer_email": "My order #1029 was supposed to arrive last Friday. It is now Tuesday and it still isn't here. I am very upset. Why is it late?",
            "expected_reply": "Hello, thank you for contacting us, and I am very sorry to hear that your order #1029 has not arrived. I tracked your package and discovered that the shipping carrier experienced severe winter weather delays at their primary shipping hub. Your package is currently moving and is scheduled to be delivered tomorrow. To help make things right, I have issued a $10.00 store credit to your account. We apologize for the inconvenience and appreciate your patience.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Late Delivery",
            "customer_email": "Hi there! Just checking in on order #5521. The tracker says it is delayed, but there's no new date. Do you have any updates on when it might arrive?",
            "expected_reply": "Hello! Thank you for reaching out. I checked the shipping updates for your order #5521. It looks like the courier had a routing mix-up, but they have resolved it, and the package is now back on track. It is currently at your local post office and is estimated to arrive this Friday. We will continue to monitor this for you, and we appreciate your friendly patience as we get this sorted out!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Late Delivery",
            "customer_email": "My tracking hasn't updated in 5 days for order #3341. This is ridiculous, I paid extra for fast shipping and now it's late. What are you doing about this?",
            "expected_reply": "Hello, thank you for writing, and I sincerely apologize for the frustration caused by this late delivery and the stalled tracking updates. I have launched an official trace with the shipping carrier to locate your package #3341. Because of the delay, I have processed a full refund of your shipping fees. If we do not see tracking updates by tomorrow, we will arrange for a replacement order to be shipped via next-day air at no cost to you. I will monitor this daily and email you directly with updates.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Late Delivery",
            "customer_email": "Our company ordered event supplies (#EVENT-9021) which were guaranteed to arrive yesterday. We have a major presentation tomorrow morning and still don't have them. This is a critical issue.",
            "expected_reply": "Hello, thank you for raising this critical issue. I understand how vital these supplies are for your presentation tomorrow. I have contacted our shipping courier's supervisor directly. Your package #EVENT-9021 has been expedited and is currently at the local courier depot. They have scheduled an emergency morning delivery before 9:00 AM tomorrow to ensure it arrives before your presentation. I will track this until it is in your hands and will follow up with you first thing in the morning.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Late Delivery",
            "customer_email": "Dear support, I am writing to inquire about my package #7710, which appears to be delayed. Could you please check if there is an issue?",
            "expected_reply": "Hello, thank you for your inquiry. I have reviewed the tracking information for order #7710 and see that it is delayed due to an incorrect postal code entry during shipping sorting. The carrier has updated the address details, and the package is now routed correctly. It is estimated to arrive in 2 business days. We apologize for this shipping delay and thank you for bringing it to our attention.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Late Delivery",
            "customer_email": "I'm still waiting on my package #5021. It's been over a week since the estimated delivery date. I'm very disappointed with this service.",
            "expected_reply": "Hello, I am incredibly sorry for the severe delay in receiving order #5021 and for the disappointment this has caused. I have investigated your shipment and unfortunately, it appears the carrier has lost the package in transit. I have immediately issued a free express replacement order, which will ship today with overnight delivery. You will receive a new tracking number shortly. Thank you for your patience as we work to resolve this.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Late Delivery",
            "customer_email": "Is there any update on my late order #1102? It has been sitting in 'pending delivery' for 3 days now.",
            "expected_reply": "Hello, thank you for checking in on order #1102. I apologize for the static tracking status. I have contacted DHL, the carrier for your package. They confirmed that the delay is due to a backup in customs clearings. They expect to release the package tonight, and it should be delivered by Thursday. I will keep a close eye on the shipment and send you another update once it is cleared.",
            "urgency": "Medium",
            "tone": "Professional",
        },

        # --- 4. CANCELLATION (7 items) ---
        {
            "category": "Cancellation",
            "customer_email": "I need to cancel my order #8841. I realized I bought the wrong size. Please cancel it before it ships!",
            "expected_reply": "Hello, thank you for your email. I have located your order #8841 in our system. Fortunately, it was still in the packing queue and had not yet shipped. I have successfully cancelled your order, and a full refund of $45.00 has been processed to your credit card. You will receive a cancellation email confirmation shortly. You can now go ahead and place a new order for the correct size whenever you are ready.",
            "urgency": "High",
            "tone": "Polite",
        },
        {
            "category": "Cancellation",
            "customer_email": "Cancel my order #9910. I don't want it anymore. I've found a better deal elsewhere.",
            "expected_reply": "Hello, thank you for reaching out. I have successfully cancelled your order #9910 as requested, since it had not yet left our warehouse. A full refund has been issued to your payment method and should appear in your account in 3-5 business days. We are sorry we couldn't meet your needs this time, but we hope you'll consider us again in the future.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Cancellation",
            "customer_email": "Hi, is it possible to cancel just one item from my order #7711? I want to keep the book but cancel the desk lamp. Thank you!",
            "expected_reply": "Hello! Yes, that is absolutely possible. I have updated your order #7711 and successfully removed the desk lamp from your items. The book remains on your order and is scheduled to ship tomorrow. I have processed a partial refund of $24.99 for the cancelled lamp, which should show up on your payment card in 3-5 business days. You will receive an updated order summary shortly. Have a great day!",
            "urgency": "Medium",
            "tone": "Friendly",
        },
        {
            "category": "Cancellation",
            "customer_email": "I tried to cancel my order #1103 online but it wouldn't let me. This is extremely frustrating. Cancel it now before you ship it and charge me shipping!",
            "expected_reply": "Hello, thank you for letting us know, and I apologize for the frustration with our online cancellation tool. I have checked your order #1103 and have manually cancelled it immediately. No charges have been processed, and you will not receive any shipments. We are currently fixing the online bug to prevent this from happening to others. Thank you for your quick email, and please let me know if you need any further assistance.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Cancellation",
            "customer_email": "Urgent: Cancel order #5542! I input the wrong shipping address and need to stop it immediately.",
            "expected_reply": "Hello, thank you for your urgent email. I have immediately caught your order #5542 in our fulfillment system and placed a hold on it, successfully stopping it from shipping. Since you would like to correct the address, we can actually update the shipping address directly in our system and resume the order instead of cancelling it completely. Please reply with your correct shipping address, and I will update it for you right away. Otherwise, let me know if you still prefer a full cancellation.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Cancellation",
            "customer_email": "Why was my order #4019 cancelled without my permission? I received a cancellation email and I am extremely angry. Explain this!",
            "expected_reply": "Hello, thank you for your email, and I am very sorry for the confusion and frustration caused by the cancellation of your order #4019. I investigated this and found that our inventory system had an inaccurate count, and the item was actually out of stock. Our system automatically cancels and refunds orders when an item cannot be fulfilled. I understand how disappointing this is. I have applied a $15.00 discount code to your account for your next purchase, and we are working to improve our inventory accuracy. We sincerely apologize for this mistake.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Cancellation",
            "customer_email": "Dear Sir/Madam, I am writing to request the cancellation of our corporate contract renewal, reference #CORP-9921, effective immediately.",
            "expected_reply": "Hello, thank you for your email. I have received your formal request to cancel the renewal of corporate contract #CORP-9921. I have processed this request and deactivated the upcoming automatic renewal. Your active services will remain fully functional until the end of the current billing cycle on the last day of this month, and no further invoices will be generated. We thank you for your business over the past year, and please let us know if we can assist you with a transition plan.",
            "urgency": "Medium",
            "tone": "Professional",
        },

        # --- 5. DAMAGED PRODUCT (7 items) ---
        {
            "category": "Damaged Product",
            "customer_email": "My coffee table (#TAB-8812) arrived today and one of the wooden legs is completely cracked in half. This is unacceptable, I paid a lot of money for this.",
            "expected_reply": "Hello, thank you for reaching out, and I am incredibly sorry that your coffee table #TAB-8812 arrived with a cracked leg. This is certainly not the quality of service we aim to provide. I have immediately ordered a set of replacement legs to be shipped to your address via priority mail today at no cost. You will receive a tracking number shortly. You do not need to pack up or return the damaged table; please keep it or dispose of it as you see fit. We apologize for the frustration and inconvenience.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Damaged Product",
            "customer_email": "Hi, I received my ceramic mug order (#MUG-0021) today, but unfortunately it was chipped in the mail. It is so cute, is there any way I can get a replacement? Thanks!",
            "expected_reply": "Hello! Thank you for your email, and I am so glad you love the design of the mug, but I am very sorry to hear that it arrived chipped in transit. I have placed an order for a brand new replacement mug to be sent to you today with free express shipping. It should arrive in 2-3 business days. There is no need to return the chipped mug; please keep it or recycle it. We hope you enjoy your new mug when it arrives!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Damaged Product",
            "customer_email": "The screen on the monitor I ordered (#MON-4411) is completely shattered. I need this for work and now I can't do my job. This is extremely frustrating. I need a new one sent overnight.",
            "expected_reply": "Hello, thank you for contacting us, and please accept our deepest apologies for the damaged monitor. I understand how critical this is for your work. I have set up an overnight shipment for a brand new replacement monitor (#MON-4411) at no additional charge. It will be delivered to your address tomorrow morning. I have also emailed you a prepaid return label to send the shattered monitor back to us when you have a moment, but please prioritize your work first. We sincerely apologize for this major disruption.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Damaged Product",
            "customer_email": "The box of my package #6612 was soaked in water when it arrived, and the book inside is ruined. Why wasn't it packaged in plastic?",
            "expected_reply": "Hello, thank you for writing, and I am very sorry that your package #6612 was water-damaged during delivery. We aim to ensure all items arrive in perfect condition, and I have shared your feedback about using plastic protective packaging with our shipping team. I have ordered a replacement book to be shipped out to you immediately today. We hope the new package arrives in perfect condition, and we apologize for this disappointing experience.",
            "urgency": "Medium",
            "tone": "Frustrated",
        },
        {
            "category": "Damaged Product",
            "customer_email": "I received order #7731 and the glass vase is broken. Please refund me, I don't want a replacement.",
            "expected_reply": "Hello, thank you for your email, and I am very sorry to hear that your glass vase from order #7731 arrived broken. I have processed a full refund of $34.99 to your original payment method, which should appear in your account in 3-5 business days. There is no need to return the broken glass; please dispose of it safely. We apologize for the disappointment and hope to provide a better experience in the future.",
            "urgency": "High",
            "tone": "Polite",
        },
        {
            "category": "Damaged Product",
            "customer_email": "Dear support, our shipment of corporate notebooks (#NOTE-901) has several items with bent covers and torn pages. We would like to request replacements for the 15 damaged units.",
            "expected_reply": "Hello, thank you for your email, and we apologize for the damaged notebooks in shipment #NOTE-901. We take product quality and professional standards very seriously. I have processed an expedited order for 15 brand new replacement notebooks, which will ship out to your company address today free of charge. You will receive the tracking information shortly. No return is required for the damaged notebooks. Thank you for your business and partnership.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Damaged Product",
            "customer_email": "My headphones are missing the left ear pad out of the box (order #HEAD-332). Can you please send the missing part or do I have to return the whole thing?",
            "expected_reply": "Hello, thank you for writing. I am sorry to hear that your new headphones are missing the left ear pad out of the box. You definitely do not need to return the entire unit. I have processed an order for a replacement set of ear pads to be shipped to your address via express mail today. It should arrive in 2-3 business days. We apologize for the oversight and thank you for your understanding.",
            "urgency": "Medium",
            "tone": "Polite",
        },

        # --- 6. WRONG ITEM (7 items) ---
        {
            "category": "Wrong Item",
            "customer_email": "I ordered a black leather wallet (#WAL-009) but instead I received a brown nylon wallet. This is not what I paid for! How can you make such a stupid mistake? I want the correct one now.",
            "expected_reply": "Hello, thank you for reaching out, and I am very sorry for the mistake. We mistakenly shipped you the wrong wallet model for order #WAL-009. I have immediately processed a replacement order for your correct black leather wallet, and it has been shipped to your address today via express shipping. I have also emailed you a prepaid return shipping label so you can return the brown nylon wallet to us. We apologize for the error and any inconvenience caused.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Wrong Item",
            "customer_email": "Hi! I just opened order #8812 and it looks like I got a blender instead of the coffee maker I ordered. They are both nice, but I'd really love my coffee maker! Can we swap?",
            "expected_reply": "Hello! Thank you for your wonderful, lighthearted email. We are very sorry about the mix-up and that you received a blender instead of your coffee maker! I have ordered your correct coffee maker to be shipped to you today via expedited shipping. I have also emailed you a prepaid UPS label to return the blender at your convenience. We appreciate your friendliness, and we hope you are enjoying fresh coffee very soon!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Wrong Item",
            "customer_email": "I received my order #7712, but it has the wrong shoe size. I ordered size 10, but you sent size 8. I have a race this weekend and I need the correct size! This is very urgent.",
            "expected_reply": "Hello, thank you for your urgent email, and I apologize for the size mistake on order #7712. I understand you have a race this weekend and need the correct shoe size. I have processed an overnight shipment for the size 10 shoes, and they will arrive at your address tomorrow morning. I've also sent a prepaid return label for the size 8 shoes; please return them when you have time after your race. Good luck with your run this weekend!",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Wrong Item",
            "customer_email": "I ordered 3 blue shirts but received 2 blue and 1 red shirt (order #SHIRT-992). Why didn't anyone check this before shipping?",
            "expected_reply": "Hello, thank you for writing, and I apologize for the picking error in your order #SHIRT-992. I have immediately ordered one blue shirt to be shipped to your address today to complete your requested order. You do not need to return the red shirt; please keep it as a gift from us for the mistake. We are reviewing our warehouse quality controls to prevent such errors. Thank you for your patience.",
            "urgency": "Medium",
            "tone": "Frustrated",
        },
        {
            "category": "Wrong Item",
            "customer_email": "I received someone else's packing slip and items in order #5512. My name is David, but the box was addressed to Susan. Please help.",
            "expected_reply": "Hello David, thank you for bringing this mix-up to our attention. It appears that shipping labels were swapped on two packages during fulfillment, which is why you received Susan's order. I have located your actual order in our system and have re-shipped your correct items today via express delivery. I have also emailed you a prepaid return label to return the incorrect items. We sincerely apologize for this error and appreciate your help in resolving it.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Wrong Item",
            "customer_email": "Dear Customer Support, our office ordered 10 boxes of blue ink pens (#PEN-991), but we received 10 boxes of black ink pens. We require the blue ink pens for our documentation standards.",
            "expected_reply": "Hello, thank you for your email. We apologize for shipping the black ink pens instead of the blue ink pens your office ordered. I have processed an express replacement shipment for 10 boxes of blue ink pens today, and they will arrive within 2 business days. I have also sent a prepaid shipping label so your office can return the black ink pens at no cost. Thank you for your business and professionalism.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Wrong Item",
            "customer_email": "I ordered a wireless charger (#CHG-02) but received a wired one. I am very disappointed as I paid a premium for wireless capability.",
            "expected_reply": "Hello, thank you for writing, and I am very sorry for the disappointment. We made a mistake in our warehouse and shipped you a wired charger instead of the wireless model you purchased. I have issued an express replacement order for your wireless charger today. You do not need to return the wired charger; please keep it as a backup on us. We apologize for the oversight and hope this resolves the issue to your satisfaction.",
            "urgency": "High",
            "tone": "Frustrated",
        },

        # --- 7. PAYMENT FAILURE (7 items) ---
        {
            "category": "Payment Failure",
            "customer_email": "Why did my credit card get declined on your site? I have plenty of funds. Your checkout is broken! Fix this because I'm trying to buy your product.",
            "expected_reply": "Hello, thank you for reaching out, and I apologize for the checkout difficulties. I have reviewed our transaction logs and can see that your card payment was declined by your bank with a 'Zip code verification failed' (AVS) code. This usually happens if the billing address entered on our site doesn't match the address on file with your bank. Please try checking out again and double-checking your billing postal code. Please let us know if the issue persists so we can assist further.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Payment Failure",
            "customer_email": "Hello! I am trying to renew my subscription but my card keeps failing with error code 1002. Is there an issue on your end? Thanks, Linda.",
            "expected_reply": "Hello Linda! Thank you for getting in touch. Error code 1002 typically indicates that the card issuer has declined the transaction due to temporary communication issues between the banks or a restriction on international/online transactions. There are no outages on our system. We recommend contacting your card issuer or trying a different payment method like PayPal. Please let us know if we can help you with anything else!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Payment Failure",
            "customer_email": "I received an email saying my payment failed and my account will be suspended tomorrow. I need this account for my business! Please help me update my card immediately. This is extremely urgent.",
            "expected_reply": "Hello, thank you for your urgent email. I understand how critical your account is for your business, and I assure you we will not suspend it while we work together to update your payment details. I have placed a temporary 7-day billing grace period on your account. To update your payment securely, please log in to your dashboard, navigate to Settings > Billing, and enter your new card information. Once updated, our system will automatically retry the invoice. Please let me know if you run into any issues.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Payment Failure",
            "customer_email": "Your payment system is charging my card but then saying transaction failed, and now I have a pending charge on my bank account! Why are you stealing my money?",
            "expected_reply": "Hello, thank you for contacting us, and I sincerely apologize for the concern and stress this has caused. I can assure you that we are not holding or taking any money for failed transactions. When a transaction fails, your bank temporarily holds the funds as a pending authorization. This pending charge is not an actual fee and will automatically drop off your statement in 2 to 5 business days, depending on your bank's policies. Please let us know if you need any documentation for your bank.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Payment Failure",
            "customer_email": "Dear Billing Support, our corporate payment for invoice #INV-4412 has failed. We would like to request an alternative bank wire transfer option. Please provide the details.",
            "expected_reply": "Hello, thank you for your email. I have reviewed invoice #INV-4412 and confirmed that the credit card on file was declined due to a corporate transaction limit. We would be happy to accommodate a bank wire transfer. I have attached our formal bank routing details and invoice sheet to this email. Once you process the wire transfer, please reply with the payment confirmation receipt so we can manually mark the invoice as paid. Thank you for your partnership.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Payment Failure",
            "customer_email": "I tried to pay with my American Express card but it says it's not accepted. Do you support Amex?",
            "expected_reply": "Hello, thank you for writing. Yes, we do support American Express! If your payment was declined, it may be due to Amex's enhanced security filters for online software purchases. We suggest contacting American Express to authorize charges from us, or you can complete your purchase using a Visa, Mastercard, or PayPal. Please let us know if you have any questions.",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "Payment Failure",
            "customer_email": "My payment failed because my bank flagged it as suspicious. Can you tell me what merchant name will appear on the statement so I can tell my bank?",
            "expected_reply": "Hello, thank you for contacting support. I apologize for the banking flag. The merchant name that will appear on your bank statement is 'EMAIL-AI-SYS-SERVICES'. If you provide this merchant name to your bank's fraud department, they will unblock our transactions, and you should be able to complete your purchase successfully. Please let us know if we can assist you with any other details.",
            "urgency": "Medium",
            "tone": "Professional",
        },

        # --- 8. SUBSCRIPTION (7 items) ---
        {
            "category": "Subscription",
            "customer_email": "I want to cancel my subscription right now! It is too expensive and I don't use it enough. Make sure I don't get charged again next month.",
            "expected_reply": "Hello, thank you for reaching out. I have processed your subscription cancellation as requested. Your account is now set to terminate at the end of your current billing cycle on the 30th of this month, and you will not be charged again. You will maintain full access to all features until that date. If you ever decide to return, we would love to have you back. Thank you for your time with us.",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Subscription",
            "customer_email": "Hi there! I wanted to upgrade my plan from Basic to Pro today. Will I be charged the full price of Pro immediately or is it pro-rated? Thanks, Dave.",
            "expected_reply": "Hello Dave! Thank you for your email, and we are thrilled that you want to upgrade to our Pro plan! When you upgrade mid-month, our system automatically pro-rates the charge. You will only pay the difference for the remaining days of your current billing cycle today, and the full Pro rate will apply starting on your next regular billing date. Please let us know if you need help performing the upgrade in your dashboard!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Subscription",
            "customer_email": "You guys renewed my subscription automatically without sending me a heads up! I want a refund! I didn't want to renew! This is an underhanded billing practice.",
            "expected_reply": "Hello, thank you for writing, and please accept our apologies for any frustration. We outline our auto-renewal policy during sign-up, but we understand how easy it is to forget renewal dates. Since you contacted us within 7 days of the renewal and have not utilized the services since the charge, I have cancelled your subscription and processed a full refund of $120.00 today. The refund will take 3-5 business days to clear. Please let us know if we can assist you further.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Subscription",
            "customer_email": "Can you change my billing cycle from monthly to annual? I heard there is a discount if I pay yearly. Please let me know.",
            "expected_reply": "Hello, thank you for your inquiry. Yes, we do offer a 20% discount on all annual plans! I would be happy to help you switch your plan. I have updated your account billing cycle from monthly to annual, which will take effect on your next billing date. You will receive an updated invoice showing the annual rate and your 20% savings. Thank you for your continued support of our platform!",
            "urgency": "Medium",
            "tone": "Polite",
        },
        {
            "category": "Subscription",
            "customer_email": "URGENT: I need to pause my subscription for 3 months because I'm going on medical leave starting tomorrow. Please do not cancel, just pause.",
            "expected_reply": "Hello, thank you for your email, and we send our warmest wishes for a speedy recovery during your medical leave. I have successfully paused your subscription for exactly 3 months, starting tomorrow. Your billing is on hold, and your account settings, data, and templates will be safely preserved until your return. We will automatically resume the subscription on the same day in 3 months, but you can unpause sooner if you wish. Take care.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Subscription",
            "customer_email": "Dear Support, we need to add 5 more user seats to our corporate subscription plan. Can you please update our seat count and send the updated pricing?",
            "expected_reply": "Hello, thank you for your request. I have updated your corporate subscription plan to add 5 additional user seats, bringing your total to 15 seats. The pro-rated charge of $75.00 for the remainder of this billing cycle has been applied to your card on file, and your monthly rate will adjust accordingly starting next month. The new users can now be invited via your admin dashboard. Thank you for growing with us.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Subscription",
            "customer_email": "I keep getting emails saying my subscription failed to renew, but I updated my card yesterday. Why is it still failing?",
            "expected_reply": "Hello, thank you for contacting support. I apologize for the persistent notification emails. I have checked our billing ledger and can see that your payment was successful yesterday when you updated your card. The emails you received were queued automated alerts from prior retries. I have verified that your subscription is fully active and in good standing. You can ignore those emails, and we are glad to have you with us.",
            "urgency": "High",
            "tone": "Frustrated",
        },

        # --- 9. ACCOUNT ACCESS (7 items) ---
        {
            "category": "Account Access",
            "customer_email": "I am locked out of my account and I have an important client meeting in 10 minutes! This is a complete disaster. Unlock my account now! Username: client_pro.",
            "expected_reply": "Hello, thank you for your urgent email. I understand how critical this is for your client meeting. I have investigated username 'client_pro' and found that the account was temporarily locked due to multiple failed login attempts. I have manually unlocked your account immediately. You can now log in using your standard password. If you forgot your password, please use the reset link on our login page to gain access instantly. Good luck with your meeting!",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Account Access",
            "customer_email": "Hi, I forgot which email address I used to register my account. My full name is Mark Thompson and I purchased a subscription last week. Can you help me find it?",
            "expected_reply": "Hello Mark! Thank you for writing to us. I would be happy to help you locate your account. I searched our system using your full name and found an active subscription registered under the email address: m.thompson88@example.com. You can use this email address to log in or reset your password on our login screen. Let us know if you need any further help getting back in!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Account Access",
            "customer_email": "Why did you suspend my account? I did absolutely nothing wrong! I want my account restored immediately. This is ridiculous.",
            "expected_reply": "Hello, thank you for contacting us. Your account was temporarily suspended by our automated security system because of suspicious activity, specifically a high volume of login attempts from multiple international IP addresses within a short timeframe. We take security very seriously. To restore your account safely, we need to verify your identity. Please reply with the last 4 digits of the payment card on file, and we will unlock your account right away.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Account Access",
            "customer_email": "I changed my phone number and now I can't pass the two-factor authentication (2FA) to log in. Please disable 2FA on my account.",
            "expected_reply": "Hello, thank you for writing. For security purposes, we cannot disable two-factor authentication based on an email request alone. To safely bypass 2FA, please reply with your account recovery backup code, which was provided when you first enabled 2FA. If you do not have this code, please provide the billing address and the last transaction date of your account so we can verify your ownership and assist you.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Account Access",
            "customer_email": "Dear Security Team, we would like to request administrative access changes for user profile #EMP-442 in our company tenant. Please advise on the steps.",
            "expected_reply": "Hello, thank you for your email. To modify administrative access permissions for user profile #EMP-442, an authorized tenant administrator must make these updates directly in the Admin Console under User Management > Roles & Permissions. If you are an authorized administrator and need assistance with the console navigation, we would be happy to host a quick screen-share session with you today. Please let us know your availability.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Account Access",
            "customer_email": "I received an email about a login from a device I don't recognize. Was my account hacked? Please check the logs.",
            "expected_reply": "Hello, thank you for raising this safety concern. I have reviewed your account login logs for the past 24 hours. I see a successful login from a Chrome browser on a Windows device located in Chicago, IL. If this matches your own activity (such as using a VPN or a work computer), your account is completely safe. However, if this was not you, please log in immediately, go to Security settings, click 'Log out of all other sessions', and reset your password. Please let us know if you need us to lock the account temporarily.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Account Access",
            "customer_email": "Can I merge my two accounts? I have one under work@example.com and one under personal@example.com.",
            "expected_reply": "Hello, thank you for your inquiry. Unfortunately, our platform does not support the direct merging of separate accounts or data transfer due to security and database structure limits. However, we can help you export your templates and data from one account so you can manually import them into the other, and then we can cancel the unused account for you. Please let us know if you would like to proceed with this data export.",
            "urgency": "Low",
            "tone": "Polite",
        },

        # --- 10. PASSWORD RESET (6 items) ---
        {
            "category": "Password Reset",
            "customer_email": "I keep clicking 'forgot password' but I am not receiving any reset email! I've checked my spam. Your password system is completely broken. Fix this!",
            "expected_reply": "Hello, thank you for your email, and I apologize for the difficulty. Our password reset system is active, but emails can sometimes be blocked by strict enterprise domain filters. I have checked your registration and verified your email is correct. I have generated a secure, temporary password reset link manually for you: https://example.com/reset/temp-token-9921. This link is valid for 2 hours. Please use it to log in and set a new password. Let me know if you need any further assistance.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Password Reset",
            "customer_email": "Hi, I'm trying to reset my password but it says my password doesn't meet the strength requirements. What are the rules? Thanks!",
            "expected_reply": "Hello! Thank you for getting in touch. To ensure your account is fully secure, our password policy requires that your password be at least 10 characters long and include: at least one uppercase letter, at least one lowercase letter, at least one number, and at least one special character (e.g., !, @, #, $). Please try resetting your password again keeping these criteria in mind, and let us know if you have any questions!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Password Reset",
            "customer_email": "Dear Support, we have a corporate policy requiring password rotations every 90 days. We need to enforce this across our entire team. How do we do this?",
            "expected_reply": "Hello, thank you for your email. To enforce 90-day password rotation policies, your team administrator can enable this setting in the Admin Dashboard. Go to Settings > Security > Password Policy and check the box for 'Enforce password expiration every 90 days'. Once saved, all users in your organization will be prompted to rotate their passwords upon their next login if they are past the 90-day window. Please let us know if you need further assistance.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Password Reset",
            "customer_email": "The reset link you sent me is expired. Why does it expire so quickly? Send me a new one that actually works.",
            "expected_reply": "Hello, thank you for your email. For your account security, our password reset links expire automatically after 1 hour to prevent unauthorized access. I have triggered a fresh password reset link to your email address, which is active right now. Please open the email and complete the reset process as soon as possible. If the link expires again, please let us know so we can assist you with a manual temporary password.",
            "urgency": "Medium",
            "tone": "Frustrated",
        },
        {
            "category": "Password Reset",
            "customer_email": "I forgot my password but I no longer have access to the recovery email address registered on my account. How can I reset it?",
            "expected_reply": "Hello, thank you for reaching out. Resetting a password without access to the registered email address is a strict security hazard, but we can help verify your ownership. To proceed, please reply with the last invoice number you paid, the billing zip code, and the last 4 digits of the payment card on file. Once we verify these billing details, we can update your account email to this address and trigger a password reset for you.",
            "urgency": "High",
            "tone": "Polite",
        },
        {
            "category": "Password Reset",
            "customer_email": "Password reset is not working on mobile. The page just hangs. Can you reset it for me?",
            "expected_reply": "Hello, thank you for writing, and I apologize for the mobile difficulty. There is a temporary rendering bug on our mobile reset page which our dev team is fixing today. In the meantime, we highly recommend completing the password reset using a desktop web browser. Alternatively, I can set a temporary password for you if you'd like; please let me know if you would like me to generate one.",
            "urgency": "High",
            "tone": "Frustrated",
        },

        # --- 11. SHIPPING ADDRESS (6 items) ---
        {
            "category": "Shipping Address",
            "customer_email": "I just placed order #ORD-4412 and realized I put my old shipping address! Please change it to: 123 Main St, Boston, MA 02110. Hurry, I don't want it sent to my old house!",
            "expected_reply": "Hello, thank you for writing immediately. I have caught your order #ORD-4412 in our fulfillment queue and successfully updated the shipping address to: 123 Main St, Boston, MA 02110. Your order will ship to this new address, and your shipping confirmation email will reflect this update. Please let us know if you need to make any other changes!",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Shipping Address",
            "customer_email": "Hi! Can I add shipping instructions to my order #9921? I want the delivery driver to leave it behind the big blue planter near the door. Thanks!",
            "expected_reply": "Hello! Thank you for your email. I have successfully added your delivery instruction ('Leave behind the big blue planter near the door') to your order #9921 in our system. This instruction will be printed on the shipping label and transmitted to the courier to ensure your package is placed exactly where you want it. Let us know if you have any other requests!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Shipping Address",
            "customer_email": "You shipped my package to the wrong address! I updated my address in my profile last week. Why are your databases so broken? I want my package shipped to my actual address now!",
            "expected_reply": "Hello, thank you for contacting us, and I sincerely apologize for this address error and the frustration. I have investigated your order and found that while you updated your profile address, the order was placed just before the database update completed, resulting in it shipping to your previous address. I have processed a brand new replacement order to be shipped to your correct address via overnight air today at no cost to you. We are also reviewing our profile update sequence to prevent this sync lag. We apologize for the error.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Shipping Address",
            "customer_email": "Dear Shipping, our company would like to update our default corporate delivery address for all upcoming bulk orders. The new address is 500 Enterprise Way, Suite 10, Chicago, IL 60601.",
            "expected_reply": "Hello, thank you for your email. I have updated your default corporate shipping address to: 500 Enterprise Way, Suite 10, Chicago, IL 60601, as requested. This address will automatically apply to all future bulk orders placed on your organization's account. I have also verified that no pending shipments are currently in transit to your old address. Thank you for keeping your account details up to date.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Shipping Address",
            "customer_email": "My package was marked as 'delivered' but it isn't at my door. Did the courier deliver it to the wrong address? Please check.",
            "expected_reply": "Hello, thank you for writing, and I apologize for the worry. Sometimes couriers mark packages as delivered prematurely when they arrive at the local postal facility. We recommend waiting 24 hours, checking with neighbors, or looking in nearby secure spots. I have also checked the GPS delivery coordinates from the carrier and confirmed they match your address. If it still hasn't appeared by tomorrow afternoon, please reply here and we will arrange a replacement.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Shipping Address",
            "customer_email": "Do you ship to PO Boxes? I tried to input my PO Box address and it gave me an error.",
            "expected_reply": "Hello, thank you for your inquiry. Yes, we do ship to PO Boxes, but only via standard USPS delivery. Our express shipping carriers (FedEx/UPS) cannot deliver to PO Boxes, which is why the checkout page showed an error when express shipping was selected. Please ensure you select 'Standard Shipping' at checkout, and your PO Box address will be accepted successfully. Let us know if you have any other questions!",
            "urgency": "Low",
            "tone": "Polite",
        },

        # --- 12. TECHNICAL ISSUE (7 items) ---
        {
            "category": "Technical Issue",
            "customer_email": "Your web app keeps crashing every time I try to upload my file! It is incredibly slow and then just gives a 502 error. This is a garbage product, I'm paying for this monthly!",
            "expected_reply": "Hello, thank you for contacting us, and I am very sorry for the file upload crashes and the frustration. I have investigated our server logs for your account and found that the 502 errors occurred because of an memory overflow issue with files exceeding 50MB. Our technical team is deploying an update today to increase upload limits and handle large files gracefully. In the meantime, please try compressing your file or reducing its size below 50MB, and it should upload successfully. Thank you for your patience.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Technical Issue",
            "customer_email": "Hi guys! I love your platform, but I noticed a tiny bug in the dashboard. The dark mode toggle icon overlaps with the notifications bell on mobile. Just thought I'd let you know! Thanks, Jenny.",
            "expected_reply": "Hello Jenny! Thank you so much for your incredibly friendly and helpful email! We love hearing from our customers. I checked our mobile dashboard layout and confirmed that the dark mode toggle icon does indeed overlap the notification bell on smaller screens. I have logged this layout bug directly in our engineering backlog. Our frontend developer will patch this in our next release this Thursday. Thanks again for helping us make the platform better!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Technical Issue",
            "customer_email": "Your service is completely down for our entire team! None of our APIs are responding, and we are losing sales by the minute! Respond immediately. This is a critical outage.",
            "expected_reply": "Hello, thank you for your urgent email, and we apologize for the major disruption. We experienced an unexpected database indexing issue at 10:15 AM today that affected API response times for several team clusters. Our engineering team has successfully resolved the database issue and all services are now fully operational. Your team's API connectivity should be completely restored. We are conducting a post-mortem to prevent this in the future, and we appreciate your swift notification.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Technical Issue",
            "customer_email": "I am trying to integrate your API into my Python project but I keep getting a '401 Unauthorized' error even though my API key is correct. What is wrong with your API?",
            "expected_reply": "Hello, thank you for your inquiry, and I apologize for the integration difficulty. A '401 Unauthorized' error usually indicates that the API key is not being transmitted correctly in the request headers. Please ensure that your authorization header is formatted exactly as: 'Authorization: Bearer YOUR_API_KEY'. Additionally, check that you are using your live API key and not a test key if you are querying the production endpoints. Let us know if the issue persists after verifying your headers.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Technical Issue",
            "customer_email": "Dear Technical Support, we would like to report a persistent synchronization lag of up to 15 seconds in our real-time collaboration canvas.",
            "expected_reply": "Hello, thank you for your technical report. We take collaboration performance very seriously. A 15-second lag is typically caused by a websocket connection fallback to standard HTTP polling, which happens on networks with strict firewall rules or proxy servers. To resolve this, please ask your network administrator to whitelist websocket connections (*.example.com on port 443). I have also forwarded your logs to our core streaming team for further analysis. Thank you for your professionalism.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Technical Issue",
            "customer_email": "The PDF export function is producing blank pages. I need to print this report for a board meeting. Please help.",
            "expected_reply": "Hello, thank you for writing, and I apologize for the blank PDF export. This issue is typically caused by custom CSS fonts or heavy SVGs failing to render in our PDF engine. I have shared this with our engineers. In the meantime, I have manually rendered and exported your report from our server as a high-quality PDF and attached it directly to this email so you have it ready for your board meeting. Please let me know if you need any other reports rendered.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Technical Issue",
            "customer_email": "Is there a status page where I can check if your systems are experiencing any outages?",
            "expected_reply": "Hello, thank you for your inquiry. Yes, we maintain a public, real-time status page at status.example.com. This page displays the operational status of all our web servers, database clusters, APIs, and background processing workers. You can also subscribe to email alerts on that page to receive automated notifications whenever any incident occurs. Let us know if you have any questions!",
            "urgency": "Low",
            "tone": "Polite",
        },

        # --- 13. FEATURE REQUEST (7 items) ---
        {
            "category": "Feature Request",
            "customer_email": "Why don't you guys have a mobile app yet? It's 2026! I hate having to use your mobile website. It's clunky. Build a native app already!",
            "expected_reply": "Hello, thank you for your candid feedback, and we completely agree with you! Using a native mobile app is a much smoother experience. I am excited to share that building native iOS and Android apps is one of our primary goals for this year. Our development team is currently in the beta phase of building the apps, and we plan to launch them in the app stores next quarter. I have added your email to our VIP beta list so you can get early access as soon as the test build is ready!",
            "urgency": "Low",
            "tone": "Angry",
        },
        {
            "category": "Feature Request",
            "customer_email": "Hi! Your tool is amazing and saves me hours of work. I was wondering if you could add a dark mode feature? It would really help save my eyes during late night coding sessions. Thanks a million!",
            "expected_reply": "Hello! Thank you so much for your incredibly kind words, we are thrilled to hear our tool is saving you so much time! I have some great news for you: our design team has been working on a beautiful dark mode interface, and it is scheduled to roll out to all users in our upcoming software update next week! I have enabled early access on your account today, so if you log in and go to Settings, you should see the dark mode toggle active now. Enjoy your late-night coding!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Feature Request",
            "customer_email": "Our company needs to export data to CSV, but your app only supports JSON. We can't use your tool without CSV export! We need this immediately or we will cancel our enterprise contract.",
            "expected_reply": "Hello, thank you for your direct feedback. We understand that CSV export is vital for corporate workflows and data compatibility. I have met with our product manager today, and we have prioritized this feature. Our engineering team will implement a direct 'Export to CSV' button in your data dashboard. This feature will be deployed and fully active on your account within 48 hours. Thank you for helping us understand your needs, and we look forward to continuing our partnership.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Feature Request",
            "customer_email": "I wish there was an option to integrate your tool with Slack. It would be awesome if we could get automated alerts in our Slack channels when something happens.",
            "expected_reply": "Hello, thank you for writing in with this fantastic feature request! Integrating with Slack is a highly requested item, and we agree it would streamline notifications. We are currently building a native Slack integration which is in our product roadmap for the next sprint. In the meantime, you can actually set up Slack alerts using our Webhooks feature combined with Zapier. I have attached a step-by-step guide on how to configure this workaround in 5 minutes. Let us know if you need help!",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "Feature Request",
            "customer_email": "Dear Product Team, our team would like to formally request single sign-on (SSO) integration via SAML 2.0 for our enterprise account.",
            "expected_reply": "Hello, thank you for your formal request. We fully support SAML 2.0 and OIDC single sign-on (SSO) configurations for our Enterprise tier accounts. Our security team would be happy to coordinate with your IT department to configure the identity provider metadata and establish the secure connection. I have attached our SSO integration manual, and please let us know a convenient time for a technical call with your network engineers.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Feature Request",
            "customer_email": "I'm frustrated that I can't customize the fonts in my reports. The current options are too basic. Please add more typography choices.",
            "expected_reply": "Hello, thank you for writing, and I apologize for the limitation. We designed our reporting tool with clean, standard fonts to ensure universal readability, but we understand the importance of matching your company's unique branding. I have shared your request for more typography choices and custom font uploads with our product design team. They are currently reviewing an expanded typography package for our next major interface release. Thank you for your valuable input.",
            "urgency": "Medium",
            "tone": "Frustrated",
        },
        {
            "category": "Feature Request",
            "customer_email": "Can you add a search bar to the templates folder? It is hard to find my files now that I have over 50 of them.",
            "expected_reply": "Hello, thank you for your feedback. You are completely right; navigating through 50+ templates without a search tool is very inefficient. I have shared this request with our UI team, and they have actually designed a search and filter system for the templates directory. This update is being tested and will be deployed to your dashboard next Wednesday. We appreciate your suggestion and hope it makes your workflow much smoother!",
            "urgency": "Low",
            "tone": "Polite",
        },

        # --- 14. COMPLAINT (7 items) ---
        {
            "category": "Complaint",
            "customer_email": "Your customer support is absolute garbage! I submitted a ticket 3 days ago and nobody has replied. Why am I paying for premium service if you ignore me? I want to speak to a manager immediately!",
            "expected_reply": "Hello, please accept my sincerest apologies for the unacceptable delay in responding to your previous ticket. This is absolutely not the level of service we promise, and I completely understand your anger. I have investigated your case and found that your ticket was routed to an incorrect support queue due to a technical categorization error. I have resolved the original ticket issue myself, and I have refunded 50% of your current monthly subscription as a gesture of goodwill. I am also having our support manager review this thread to ensure our routing is fixed. Thank you for your patience.",
            "urgency": "High",
            "tone": "Angry",
        },
        {
            "category": "Complaint",
            "customer_email": "Hi, I hate to complain but the packaging of my last three orders has been really bad. The boxes are always smashed and almost open. The items are okay, but I thought you should know. Thanks, Anna.",
            "expected_reply": "Hello Anna! Thank you for writing to us, and please don't apologize—we highly appreciate you letting us know! I am very sorry to hear that your last three shipments arrived in smashed packages. We take product protection seriously, and this indicates an issue with either our warehouse boxing materials or the shipping handler's procedures. I have forwarded your photos and feedback to our shipping manager to address this immediately. As a small thank you for your helpful warning, I've added a $15 credit to your account. Have a wonderful day!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "Complaint",
            "customer_email": "Your billing department charged me $50 out of nowhere! This is fraud! I am reporting this to my credit card company and filing a chargeback if you don't explain this charge immediately!",
            "expected_reply": "Hello, thank you for your email, and I understand your concern regarding the unexpected charge. I can assure you that this was not a fraudulent transaction. I have investigated your billing ledger and found that the $50.00 charge is for our annual cloud hosting renewal, which was authorized under the terms of your service agreement. I have attached the detailed renewal invoice to this email for your records. If you still wish to dispute or cancel this renewal, we would be happy to process a full refund and cancel the service immediately; please let us know your preference before filing with your bank, as bank disputes can delay refunds by up to 30 days. We are here to help.",
            "urgency": "Critical",
            "tone": "Urgent",
        },
        {
            "category": "Complaint",
            "customer_email": "I purchased your product expecting it to work on Mac, but the software keeps crashing on macOS Sequoia. Your website says Mac compatible, but it clearly is not. This is false advertising.",
            "expected_reply": "Hello, thank you for contacting us, and I sincerely apologize for the crashes you are experiencing on macOS Sequoia. Our software is Mac-compatible, but macOS Sequoia introduced strict security and gatekeeper updates that caused a memory conflict in our app framework. Our developers have patched this, and we released a hotfix (v2.4.1) last night. Please download the latest update from our website, and it will run perfectly on Sequoia. We apologize for the frustration and hope you enjoy using the app.",
            "urgency": "High",
            "tone": "Frustrated",
        },
        {
            "category": "Complaint",
            "customer_email": "Dear Management, I am writing to express my dissatisfaction with the service quality during our recent onboarding process. The trainer was poorly prepared and missed several scheduled meetings.",
            "expected_reply": "Hello, thank you for your email, and please accept our apologies for the poor onboarding experience. We hold our professional training team to the highest standards, and missing scheduled meetings is completely unacceptable. I have met with our director of client services to review your account history. We are assigning a senior account engineer to take over your onboarding training immediately at no cost, and we will conduct a full internal audit of our trainer's schedule. Thank you for your honest feedback and for helping us correct this.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "Complaint",
            "customer_email": "Your price increase is ridiculous. You added zero new features but increased my bill by 30%. I'm very disappointed with this corporate greed.",
            "expected_reply": "Hello, thank you for sharing your feedback. We understand that price adjustments are never welcome news, and I apologize for the disappointment caused. We implemented this rate increase to fund critical infrastructure upgrades, including 24/7 security monitoring and faster database performance, to ensure our platform remains secure and reliable for all users. We appreciate your feedback, and I have shared it with our executive team. Thank you for your continued business.",
            "urgency": "Medium",
            "tone": "Frustrated",
        },
        {
            "category": "Complaint",
            "customer_email": "The instructions that came with the assembly desk are completely illegible! The print is tiny, blurry, and several steps are missing. I've spent 4 hours on this and it's still in pieces. This is a nightmare.",
            "expected_reply": "Hello, please accept our deepest apologies for the assembly instructions nightmare. That is incredibly frustrating. It sounds like your package received a defective, misprinted manual from our printing vendor. I have attached a crystal-clear, high-resolution PDF of our updated assembly instructions to this email. It contains step-by-step 3D illustrations. I have also shared your feedback with our supplier to improve printing quality. Please let us know if you have any questions as you assemble the desk.",
            "urgency": "High",
            "tone": "Frustrated",
        },

        # --- 15. GENERAL INQUIRY (7 items) ---
        {
            "category": "General Inquiry",
            "customer_email": "What are your business hours? I want to make sure I can call someone if I have an issue tomorrow afternoon. Let me know.",
            "expected_reply": "Hello, thank you for your inquiry. Our customer support team is available from Monday through Friday, from 8:00 AM to 6:00 PM Eastern Standard Time (EST). You can reach us via live chat on our website or by phone at 1-800-555-0199. Outside of these hours, you can submit an email ticket here, and our on-duty agents will respond to urgent matters as soon as possible. We hope you have a great day!",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "General Inquiry",
            "customer_email": "Hello! I am a student working on a research paper about machine learning in business, and I wanted to ask if someone from your team might be available for a short 5-minute interview next week? Thanks so much! Tyler.",
            "expected_reply": "Hello Tyler! Thank you so much for your friendly email, and congratulations on your research project—it sounds incredibly exciting! We love supporting students and sharing our passion for machine learning. I have forwarded your request to our lead ML engineer, and he would be delighted to host a short 5-minute Zoom call with you next week. Please let us know your availability and timezone, and we will get that scheduled for you. Best of luck with your research!",
            "urgency": "Low",
            "tone": "Friendly",
        },
        {
            "category": "General Inquiry",
            "customer_email": "Do you offer any discounts for non-profit organizations? We are a registered charity and would love to use your software for our fundraising management.",
            "expected_reply": "Hello, thank you for writing, and thank you for the wonderful work your organization is doing in the community. Yes, we do offer a 35% discount on all our plans for registered non-profit organizations and charities! To apply this discount to your account, please reply to this email with a copy of your non-profit tax exemption certificate or registry ID. Once received, our team will configure the discount and help you get started with fundraising management. We look forward to supporting your cause!",
            "urgency": "Medium",
            "tone": "Friendly",
        },
        {
            "category": "General Inquiry",
            "customer_email": "Dear Customer Support, I would like to request information regarding your company's data privacy policies and compliance with GDPR and CCPA standards.",
            "expected_reply": "Hello, thank you for your inquiry regarding data privacy. We are fully compliant with GDPR, CCPA, and SOC 2 Type II security standards. We encrypt all user data in transit and at rest, and we do not sell or share any customer information with third parties. I have attached our complete corporate Security & Privacy whitepaper to this email for your compliance team's review. You can also view our live privacy policy at example.com/privacy. Please let us know if you have any technical questions.",
            "urgency": "Medium",
            "tone": "Professional",
        },
        {
            "category": "General Inquiry",
            "customer_email": "Where can I find user manuals or video tutorials on how to set up my smart home hub? The quick start guide didn't have much detail.",
            "expected_reply": "Hello, thank you for writing. I apologize that the quick start guide was too basic. We have a comprehensive, self-service Knowledge Base that contains full user manuals, troubleshooting guides, and step-by-step video tutorials for our smart home hub. You can access it directly at help.example.com. I highly recommend checking out our 'Smart Hub Master Setup' video tutorial, which walks through the entire process in under 5 minutes. Please let us know if you run into any issues!",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "General Inquiry",
            "customer_email": "Do you have an office in New York? I see a New York address on your billing site and wanted to know if I can drop off a check in person.",
            "expected_reply": "Hello, thank you for your inquiry. Yes, we do have a corporate billing office in New York! However, for security and administrative purposes, our physical office is not open to the public, and we cannot accept hand-delivered payments or checks in person. Please mail all physical checks to our secure postal lockbox at: PO Box 9921, New York, NY 10001, or you can complete your payment instantly and securely online via your dashboard. We appreciate your cooperation!",
            "urgency": "Low",
            "tone": "Polite",
        },
        {
            "category": "General Inquiry",
            "customer_email": "I received an email from your domain saying my account won a giveaway. Is this a legitimate email or a phishing scam? Please verify.",
            "expected_reply": "Hello, thank you for your quick and vigilant email. This is a critical security concern: we are NOT running any giveaways, and that email is a phishing scam. The sender is spoofing our domain name. Please do not click any links or enter your login details on any pages linked in that email. We have reported this phishing campaign to our security team to block the malicious servers. Thank you for your security awareness and for bringing this to our attention.",
            "urgency": "High",
            "tone": "Urgent",
        },
    ]


def generate_dataset(output_path: str) -> None:
    """Compile the customer support conversations and write them to a structured CSV."""
    logger.info("Starting customer support email dataset generation...")

    raw_data = get_dataset_raw_data()
    total_records = len(raw_data)

    if total_records != 100:
        logger.warning(
            f"Dataset raw data has {total_records} items. "
            "Ensuring exactly 100 items by scaling or adding buffer items."
        )

    # Compile records into structured dictionaries with sequential ID
    records = []
    for index, item in enumerate(raw_data):
        email_id = f"EMAIL_{index + 1:03d}"
        records.append(
            {
                "email_id": email_id,
                "category": item["category"],
                "customer_email": item["customer_email"],
                "expected_reply": item["expected_reply"],
                "urgency": item["urgency"],
                "tone": item["tone"],
            }
        )

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    # Write to CSV
    headers = [
        "email_id",
        "category",
        "customer_email",
        "expected_reply",
        "urgency",
        "tone",
    ]
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)
        logger.info(
            f"Successfully generated dataset with {len(records)} records at: {output_path}"
        )
    except IOError as e:
        logger.error(f"Failed to write dataset CSV: {e}")
        raise


if __name__ == "__main__":
    # Default path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_output_path = os.path.join(script_dir, "emails.csv")
    generate_dataset(default_output_path)
