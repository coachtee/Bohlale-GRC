from .models import REQUIRED_INPUTS, ManagementReview, ManagementReviewInputRecord


def create_review(organisation, **fields):
    review = ManagementReview.objects.create(organisation=organisation, **fields)
    for label in REQUIRED_INPUTS:
        ManagementReviewInputRecord.objects.create(review=review, label=label)
    return review
