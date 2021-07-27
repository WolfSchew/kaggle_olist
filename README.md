# kaggle_olist

Based on the kaggle dataset of the brazilian online market place Olist at: https://www.kaggle.com/olistbr/brazilian-ecommerce

We want to use this dataset to do some data analysis regarding the profitability of the sellers Olist allows to use their platform. For that analysis we use some basic assumptions:

Revenue

    Olist takes a 10% cut on the product price (excl. freight) of each order delivered.
    Olist charges 80 BRL by month per seller.

Cost

In the long term, bad customer experience has business implications: low repeat rate, immediate customer support cost, refunds or unfavorable word of mouth communication. We will assume that we have an estimate measure of the monetary cost for each bad review:

    a review score of 1 star costs 100 BRL
    a review score of 2 stars costs 50 BRL
    a review score of 3 stars costs 40 BRL
    review scores of 4 or 5 stars aren't associated with additional costs

In addition, Olist’s IT costs (servers, etc…) increase with the amount of orders processed, albeit less and less rapidly (scale effects). For the sake of simplicity, we will consider Olist’s total cumulated IT Costs to be proportional to the square-root of the total cumulated number of orders approved. The IT department also told you that since the birth of the marketplace, cumulated IT costs have amounted to 500,000 BRL.

Therefore the question we want to answer in the end is:

    Should Olist remove underperforming sellers from its marketplace?

To analyse the impact of removing the worse sellers from Olist's marketplace, we can start with a what-if analysis: What would have happened if Olist had never accepted these sellers in the first place? For that:

Step 1: Compute, for each seller_id, and cumulated since the beginning:

    The revenues it brings
    The costs associated with all its bad reviews
    The resulting profits (revenues - costs)
    The number of orders (it will impact overall IT costs)

Step 2: We can then sort sellers by increasing profits for Olist, and for each number of sellers to remove, compute the financial impact it would have made had they never been accepted on the platform. We may find an optimal number of sellers to remove that maximizes Olist's profit margin.
