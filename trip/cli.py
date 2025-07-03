import click
import pandas as pd

from .cleaning   import clean_csv
from .itinerary  import generate_itinerary
from .budget     import calculate_budget

@click.command(help="Generate itinerary & budget from a raw CSV")
@click.argument("input_csv",  type=click.Path(exists=True))
@click.argument("out_clean",  type=click.Path())
@click.argument("out_itin",   type=click.Path())
@click.argument("out_budget", type=click.Path())
def main(input_csv, out_clean, out_itin, out_budget):
    # 1) Clean
    df_raw   = pd.read_csv(input_csv)
    df_clean = clean_csv(df_raw)
    df_clean.to_csv(out_clean, index=False)
    click.echo(f"Cleaned CSV → {out_clean}")

    # 2) Itinerary
    df_itin = generate_itinerary(df_clean)
    df_itin.to_csv(out_itin, index=False)
    click.echo(f"Itinerary CSV → {out_itin}")

    # 3) Budget
    df_budget = calculate_budget(df_itin)
    df_budget.to_csv(out_budget, index=False)
    click.echo(f"Budget CSV → {out_budget}")

if __name__ == "__main__":
    main()
