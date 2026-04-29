# Collection and Analysis of Municipal Reporting App Data
by Hyejin Cho, Svitlana Glibova, Patrick Martens, Andrew Naydenov

### Requirements
* Highly recommended to create a Python virtual environment as defined in `pyproject.toml`
* Recommended to create a HuggingFace API token and store in `.env.secret` at the root level of this project - these notebooks do not aggressively call to the HF API, but you will be warned that unauthenticated requests are subject to tighter rate limiting.

### Notes
* Apple frequently changes the format of headers they return on requests, and it is possible that the script used to retrieve results may not work on future attempts - keeping a backup of the data you retrieve is always a good idea.

### Project Structure
```
├── README.md
├── initial_needfinding # analysis of Apple App Store & Google Play Store reviews
│   ├── analysis.ipynb
│   ├── data
│   │   ├── reviews
│   │   │   ├── apple # pre-collected Apple App Store reviews
│   │   │   │   ├── FindItFixIt.csv 
│   │   │   │   ├── SanJose311.csv
│   │   │   │   └── SeeClickFix.csv
│   │   │   ├── combined 
│   │   │   │   └── CombinedReviews.csv
│   │   │   └── google # pre-collected Google Play Store reviews
│   │   │       ├── FindItFixit.csv
│   │   │       ├── SanJose311.csv
│   │   │       └── SeeClickFix.csv
│   │   └── sentiment_analysis # sentiment analysis reviews
│   │       ├── Classified-FindItFixIt.csv
│   │       ├── Classified-SanJose311.csv
│   │       ├── Classified-SeeClickFix.csv
│   │       ├── NegativePhraseClusters.docx
│   │       ├── NegativeSubset.csv
│   │       ├── PositivePhraseClusters.docx
│   │       └── PositiveSubset.csv
│   └── viz # visualizations
│       ├── CombinedApps.png
│       ├── FindItFixIt.png
│       ├── NegativeThemes.png
│       ├── PositiveThemes.png
│       ├── SanJose311.png
│       ├── SeeClickFix.png
│       ├── WordCloud-FindItFixIt.png
│       ├── Wordcloud-SanJose311.png
│       └── Wordcloud-SeeClickFix.png
├── prototype_evaluation # survey result evaluation for initial and final prototypes
│   ├── data
│   │   └── surveys
│   │       ├── normalized_results.csv
│   │       └── survey_results.csv
│   ├── final_prototype
│   │   └── evaluation.ipynb
│   └── initial_prototype
│       └── evaluation.ipynb
├── pyproject.toml
├── scripts # scripts used to retrieve app store reviews
│   ├── apple
│   │   ├── get_reviews.ipynb
│   │   └── scraper.py
│   └── google
│       └── get_reviews.ipynb
└── uv.lock
```