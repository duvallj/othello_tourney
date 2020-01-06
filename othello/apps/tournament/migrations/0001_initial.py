# Generated by Django 3.0.1 on 2020-01-06 00:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GameModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timelimit', models.IntegerField()),
                ('black_score', models.IntegerField()),
                ('white_score', models.IntegerField()),
                ('winner', models.CharField(choices=[('@', 'Black'), ('o', 'White'), ('?', 'None'), ('.', 'Tie')], default='?', max_length=1)),
                ('by_forfeit', models.BooleanField(default=False)),
                ('played_when', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='PlayerModel',
            fields=[
                ('id', models.CharField(max_length=15, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='TournamentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tournament_name', models.CharField(max_length=255)),
                ('played_when', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SetModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('winner', models.CharField(choices=[('@', 'Black'), ('o', 'White'), ('?', 'None'), ('.', 'Tie')], default='?', max_length=1)),
                ('completed', models.BooleanField(default=False)),
                ('played_when', models.DateField(auto_now=True)),
                ('black', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='black_sets', to='tournament.PlayerModel')),
                ('black_from_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_black_sets', to='tournament.SetModel')),
                ('in_tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sets', to='tournament.TournamentModel')),
                ('loser_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='loser_from_set', to='tournament.SetModel')),
                ('white', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='white_sets', to='tournament.PlayerModel')),
                ('white_from_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='to_white_sets', to='tournament.SetModel')),
                ('winner_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner_from_set', to='tournament.SetModel')),
            ],
        ),
        migrations.CreateModel(
            name='MoveModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('board', models.CharField(max_length=100)),
                ('to_move', models.CharField(choices=[('@', 'Black'), ('o', 'White'), ('?', 'None')], max_length=1)),
                ('in_game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moves', to='tournament.GameModel')),
            ],
        ),
        migrations.AddField(
            model_name='gamemodel',
            name='black',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='black_games', to='tournament.PlayerModel'),
        ),
        migrations.AddField(
            model_name='gamemodel',
            name='in_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='tournament.SetModel'),
        ),
        migrations.AddField(
            model_name='gamemodel',
            name='white',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='white_games', to='tournament.PlayerModel'),
        ),
    ]
