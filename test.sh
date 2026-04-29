docker exec -it contact_diary_web python manage.py test contacts --verbosity=2
docker exec -it contact_diary_web python manage.py createsuperuser