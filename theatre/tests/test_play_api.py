import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from theatre.models import Play, Performance, TheatreHall, Genre, Actor
from theatre.serializers import PlaySerializer, PerformanceSerializer, PlayDetailSerializer, PlayListSerializer

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
        "duration": 90,
    }
    defaults.update(params)

    return Play.objects.create(**defaults)


def sample_genre(**params):
    defaults = {
        "name": "Drama",
    }
    defaults.update(params)

    return Genre.objects.create(**defaults)


def sample_actor(**params):
    defaults = {"first_name": "Bohdan", "last_name": "Stupka"}
    defaults.update(params)

    return Actor.objects.create(**defaults)


def sample_performance(**params):
    theatre_hall = TheatreHall.objects.create(
        name="Green", rows=25, seats_in_row=30
    )

    defaults = {
        "show_time": "2024-01-03 19:00:00",
        "play": None,
        "theatre_hall": theatre_hall,
    }
    defaults.update(params)

    return Performance.objects.create(**defaults)


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


class UnauthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "Test12345",
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        sample_play()
        play_with_genre_and_actor = sample_play()

        genre1 = Genre.objects.create(name="Drama")
        actor1 = Actor.objects.create(first_name="Bohdan", last_name="Stupka")

        play_with_genre_and_actor.genres.add(genre1)
        play_with_genre_and_actor.actors.add(actor1)

        res = self.client.get(PLAY_URL)
        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_movie_by_title(self):
        play1 = sample_play(title="Play1")
        play2 = sample_play(title="Play2")

        res = self.client.get(PLAY_URL, {"title": f"{play1.title}"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_play_by_genres(self):
        play1 = sample_play(title="Play1")
        play2 = sample_play(title="Play2")
        play3 = sample_play(title="Play without filter")

        genre1 = sample_genre(name="genre1")
        genre2 = sample_genre(name="genre2")

        play1.genres.add(genre1)
        play2.genres.add(genre2)

        res = self.client.get(PLAY_URL, {"genres": f"{genre1.id},{genre2.id}"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)
        serializer3 = PlayListSerializer(play3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_play_by_actors(self):
        play1 = sample_play(title="Play1")
        play2 = sample_play(title="Play2")
        play3 = sample_play(title="Play without filter")

        actor1 = sample_actor(first_name="actor1")
        actor2 = sample_actor(first_name="actor2")

        play1.actors.add(actor1)
        play2.actors.add(actor2)

        res = self.client.get(PLAY_URL, {"actors": f"{actor1.id},{actor2.id}"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)
        serializer3 = PlayListSerializer(play3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_retrieve_play_detail(self):
        play = sample_play()
        play.genres.add(Genre.objects.create(name="Drama"))

        url = detail_url(play.id)

        res = self.client.get(url)

        serializer = PlayDetailSerializer(play)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_play_forbidden(self):
        payload = {
            "title": "Test title",
            "description": "Test description",
            "duration": 99,
        }

        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com",
            "Test12345",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_movie(self):
        payload = {
            "title": "Test title",
            "description": "Test description",
            "duration": 99,
        }

        res = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(play, key))

    def test_create_play_with_genres(self):
        genre1 = sample_genre(name="genre1")
        genre2 = sample_genre(name="genre2")
        payload = {
            "title": "Test title",
            "description": "Test description",
            "duration": 99,
            "genres": [genre1.id, genre2.id]
        }

        res = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=res.data["id"])
        genres = play.genres.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(genres.count(), 2)
        self.assertIn(genre1, genres)
        self.assertIn(genre2, genres)

    def test_create_play_with_actors(self):
        actor1 = sample_actor(first_name="genre1")
        actor2 = sample_actor(first_name="genre2")

        payload = {
            "title": "Test title",
            "description": "Test description",
            "duration": 99,
            "actors": [actor1.id, actor2.id]
        }

        res = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=res.data["id"])
        actors = play.actors.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(actors.count(), 2)
        self.assertIn(actor1, actors)
        self.assertIn(actor2, actors)

    def test_delete_play_not_allowed(self):
        play = sample_play()
        url = detail_url(play.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
